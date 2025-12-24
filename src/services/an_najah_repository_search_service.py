import json
from langdetect import detect

from src.opensearch.abstract_classes.ABC_client import ABCClient
from src.query_utils.suggest_query import build_suggest_query
from src.query_utils.query_preprocessor import prepare_input
from src.query_utils.full_text_query import build_hybrid_query_pipeline
from src.queries_generation.query_generation import Query
from src.opensearch.mapping import ProjectMapping
from src.models.abstract_classes.generative_model import ABCGenerativeModel


class AnNajahRepositorySearchService:
    """
    Service for indexing and searching articles in OpenSearch.
    """

    def __init__(
        self,
        index: str,
        client: ABCClient,
        query_generator: Query,
        mapping: ProjectMapping,
        generative_model: ABCGenerativeModel,
    ):
        """
            Class constructor inject the required dependencies via the parameters
        Args:
            index (str): The name of the index to operate on.
            client (ABCClient): An instance of ABCClient to interact with OpenSearch.
        """
        self._client = client
        self._index = index
        self.mapping = mapping
        self._query_generator = query_generator
        self._generative_model = generative_model

    def search_articles(self, query: dict):
        """simple search function for custom queries

        Args:
            query (dict): The search query as a dictionary.

        Returns:
            dict: The search results.
        """
        es = self._client.get_client()
        return es.search(index=self._index, body=query)

    def generate_query(self, user_prompt: str):
        """Generate a search query based on the user's prompt.

        Args:
            user_prompt (str): The user's input or query for generating the search.

        Returns:
            documents: the results of the search based on the generated query.
            generated_query: the generated query string.
        """

        generated_query_str = self._query_generator.generate_opensearch_query(
            user_prompt, self.mapping.create_configurations()
        )
        try:
            generated_query = (
                json.loads(generated_query_str)
                if isinstance(generated_query_str, str)
                else generated_query_str
            )
        except Exception as e:
            print("Error parsing generated query string:", e)
            generated_query = {}
        result = self.search_articles(generated_query)
        return result, generated_query_str

    def client_health(self):
        """Check the health of the OpenSearch client."""
        es = self._client.get_client()
        return es.cluster.health()

    def suggest(self, prefix: str, limit: int = 8) -> list[str]:
        """
        Return autocomplete suggestions for a user-typed query prefix.

        The method:
        - Normalizes the prefix and enforces a minimum length (>= 3 chars).
        - Builds an OpenSearch query via `build_suggest_query`.
        - Searches the index and extracts candidate suggestions from `_source`
        (titles in English/Arabic and author names).
        - De-duplicates suggestions case-insensitively and returns up to `limit`.

        Args:
            prefix: Partial query text typed by the user.
            limit: Maximum number of suggestions to return.

        Returns:
            A list of unique suggestion strings (titles/authors), capped at `limit`.
        """
        prefix = (prefix or "").strip()
        if len(prefix) < 3:
            return []
        fetch_size = min(80, max(25, limit * 8))  # e.g., limit=8 -> 64
        query = build_suggest_query(prefix, fetch_size=fetch_size)

        res = self.search_articles(query=query)

        hits = res.get("hits", {}).get("hits", [])

        seen = set()
        out = []

        for hit in hits:
            src = hit.get("_source", {}) or {}

            # titles (en/ar)
            title = src.get("title", {}) or {}
            for lang in ("en", "ar"):
                t = (title.get(lang) or "").strip()
                key = t.lower()
                if t and key not in seen:
                    seen.add(key)
                    out.append(t)
                    if len(out) >= limit:
                        return out

            # authors
            authors = src.get("author", [])
            if isinstance(authors, str):
                authors = [authors]
            for a in authors or []:
                a = (a or "").strip()
                key = a.lower()
                if a and key not in seen:
                    seen.add(key)
                    out.append(a)
                    if len(out) >= limit:
                        return out

        return out[:limit]

    def user_query(self, query: str) -> dict:
        """
        Build the OpenSearch query body for a user query (hybrid lexical + semantic).

        This method prepares the input query by:
        - Detecting language ("en"/"ar").
        - Extracting temporal expressions and geographic references.
        - Building a hybrid OpenSearch DSL using `build_hybrid_query_pipeline`.

        Note:
            This method currently returns the constructed OpenSearch request body
            (DSL). Executing the search is handled elsewhere.

        Args:
            q: Raw user query text.

        Returns:
            An OpenSearch query body (dictionary) suitable for `search(...)`.
        """

        lang, lexical25_clean_query, semantic_vector_query, temporals, geo_refs = (
            prepare_input(query)
        )

        # 3) Search pipeline normalization (hybrid DSL)
        body = build_hybrid_query_pipeline(
            lexical25_text=lexical25_clean_query,
            semantic_query_vector=semantic_vector_query,
            temporal_expressions=temporals,
            geo_refs=geo_refs,
            num_candidates=100,
            lang=lang,
        )

        return body

    def generate_answer(self, user_input: str) -> str:
        """
        Generate a response based on the input user query and retrieved documents.

        Args:
            user_input (str): The input query string.
        Returns:
            str: The generated response.
        """

        if not user_input or user_input.strip() == "":
            return "Please provide a valid query."

        # Detect user's input language
        try:
            users_input_language = detect(user_input)
        except Exception:
            users_input_language = "en"  # default fallback

        preferred_lang = (
            users_input_language if users_input_language in {"en", "ar"} else "en"
        )
        fallback_lang = "ar" if preferred_lang == "en" else "en"
        
        # 1) Formulate a self-contained query
        formulated_query = self._generative_model.formulate_query(user_input)
        # 2) Search for relevant documents
        os_query = self.user_query(formulated_query)
        search_results = self.search_articles(os_query)
        # 3) Extract relevant documents' text in preferred language
        retrieved_docs = set()
        for hit in search_results.get("hits", {}).get("hits", []):
            abstract = (hit.get("_source", {}) or {}).get("abstract", {}) or {}
            preferred_text = abstract.get(preferred_lang)
            fallback_text = abstract.get(fallback_lang)

            # Keep the text in the user's language when available; otherwise, fall back once.
            if preferred_text:
                retrieved_docs.add(preferred_text)
            elif fallback_text:
                retrieved_docs.add(fallback_text)

        if not retrieved_docs:
            return "No relevant documents found to generate an answer."
        # 4) Generate the answer using the generative model
        answer = self._generative_model.generate(formulated_query, retrieved_docs)
        return answer
