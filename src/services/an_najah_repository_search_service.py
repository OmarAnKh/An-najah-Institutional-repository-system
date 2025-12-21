from src.opensearch.abstract_classes.ABC_client import ABCClient
from src.query_utils.suggest_query import build_suggest_query
from src.query_utils.query_preprocessor import prepare_input
from src.query_utils.full_text_query import build_hybrid_query_pipeline
from src.queries_generation.query_generation import QueryGeneration, Query

from src.queries_generation.query_generation import Query
from src.opensearch.mapping import ProjectMapping
import json


class AnNajahRepositorySearchService:
    """
    Service for indexing and searching articles in OpenSearch.
    """

    def __init__(
        self,
        index: str,
        client: ABCClient,
        query_generator: Query,
        mapping=ProjectMapping,
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

    def user_query(self, q: str) -> dict:
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
            prepare_input(q)
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
