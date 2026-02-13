import json
from langdetect import detect

from src.opensearch.abstract_classes.ABC_client import ABCClient
from src.query_utils.suggest_query import build_suggest_query
from src.query_utils.query_preprocessor import prepare_input
from src.query_utils.full_text_query import build_hybrid_query_pipeline
from src.queries_generation.abstract_classes import ABCQueryGeneration
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
        query_generator: ABCQueryGeneration,
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

    def search_using_query(self, query: dict, size: int = 8) -> dict:
        """simple search function for custom queries

        Args:
            query (dict): The search query as a dictionary.

        Returns:
            dict: The search results.
        """
        es = self._client.get_client()

        # Always exclude embeddings from responses (large payload, not needed by API clients).
        # Use OpenSearch's source filtering (server-side) + a defensive post-filter below.
        result = es.search(
            index=self._index,
            body=query,
            _source_excludes=["abstract_vector"],
            size=size,
        )

        hits = (result.get("hits") or {}).get("hits") or []
        for hit in hits:
            src = hit.get("_source")
            if isinstance(src, dict):
                src.pop("abstract_vector", None)

        return result

    def generate_query(self, user_prompt: str, size: int = 8) -> tuple[dict, str]:
        """Generate a search query based on the user's prompt.

        Args:
            user_prompt (str): The user's input or query for generating the search.
            size (int): The number of search results to retrieve (default: 8).

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
        result = self.search_using_query(generated_query, size=size)
        return result, generated_query_str

    def client_health(self):
        """Check the health of the OpenSearch client."""
        es = self._client.get_client()
        return es.cluster.health()

    def suggest(self, prefix: str, limit: int = 5) -> list[str]:
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

        # Prefer suggestions in the same language as the typed prefix (en/ar only).
        try:
            detected_lang = detect(prefix)
            preferred_lang = detected_lang if detected_lang in {"en", "ar"} else "en"
        except Exception:
            preferred_lang = "en"

        fetch_size = min(80, max(25, limit * 8))  # e.g., limit=8 -> 64
        query = build_suggest_query(prefix, fetch_size=fetch_size)

        res = self.search_using_query(query=query)

        hits = res.get("hits", {}).get("hits", [])

        seen = set()
        out = []

        for hit in hits:
            src = hit.get("_source", {}) or {}

            # titles (en/ar)
            title = src.get("title", {}) or {}

            t = (title.get(preferred_lang) or "").strip()
            key = t.lower()
            if t and key not in seen:
                seen.add(key)
                out.append(t)
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

    def generate_answer(self, user_input: str) -> tuple[str, list[dict]]:
        """
        Generate a response based on the input user query and retrieved documents.

        Args:
            user_input (str): The input query string.
        Returns:
            tuple[str, list[dict]]: Generated answer text and citation metadata.
        """

        if not user_input or user_input.strip() == "":
            return "Please provide a valid query.", []

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
        if not formulated_query:
            formulated_query = user_input
        # 2) Search for relevant documents
        os_query = self.user_query(formulated_query)
        search_results = self.search_using_query(os_query)
        # 3) Extract relevant documents' text in preferred language
        hits = search_results.get("hits", {}).get("hits", [])

        retrieved_docs = set()
        citations = []
        seen_items = set()

        for hit in hits:
            source = hit.get("_source", {}) or {}
            abstract = source.get("abstract", {}) or {}
            preferred_text = abstract.get(preferred_lang)
            fallback_text = abstract.get(fallback_lang)

            # Keep the text in the user's language when available; otherwise, fall back once.
            if preferred_text:
                retrieved_docs.add(str(preferred_text))
            elif fallback_text:
                retrieved_docs.add(str(fallback_text))

            item_uuid = source.get("item_uuid")
            if not item_uuid:
                continue

            title_obj = source.get("title") or {}

            if isinstance(title_obj, dict):
                title = (
                    title_obj.get(preferred_lang) or title_obj.get(fallback_lang) or ""
                )
            elif isinstance(title_obj, str):
                title = title_obj
            else:
                title = ""

            if not title:
                dc_title = source.get("dc_title")
                if isinstance(dc_title, dict):
                    title = (
                        dc_title.get(preferred_lang)
                        or dc_title.get(fallback_lang)
                        or ""
                    )
                elif isinstance(dc_title, str):
                    title = dc_title

            title = title.strip() if isinstance(title, str) else ""
            if not title:
                title = "Untitled"

            snippet_val = preferred_text or fallback_text or ""
            snippet = snippet_val if isinstance(snippet_val, str) else str(snippet_val)

            if item_uuid not in seen_items:
                seen_items.add(item_uuid)
                citations.append(
                    {
                        "item_uuid": str(item_uuid),
                        "title": title,
                        "snippet": snippet,
                    }
                )

        if not retrieved_docs:
            return "No relevant documents found to generate an answer.", []

        # 4) Generate the answer using the generative model
        try:
            answer = self._generative_model.generate(formulated_query, retrieved_docs)
        except Exception as exc:
            return f"No relevant documents found to generate an answer. ({exc})", []

        answer_text = answer if isinstance(answer, str) else str(answer)

        normalized_answer = answer_text.lower()
        if "no relevant" in normalized_answer or "no available" in normalized_answer:
            citations = []

        return answer_text, citations

    def generate_advanced_query(self, user_prompt: str) -> dict:
        """Generate an advanced OpenSearch query object based on a user prompt.

        Args:
            user_prompt (str): The user's input or query for generating the search.

        Returns:
            dict: The generated OpenSearch query object.
        """

        raw_query = self._query_generator.generate_opensearch_query(
            user_prompt, self.mapping.create_configurations()
        )

        # Accept both dict and string outputs from the generator.
        if isinstance(raw_query, dict):
            return raw_query

        if not isinstance(raw_query, str):
            return {}

        cleaned = raw_query.strip()

        # Drop common markdown fences (```json ... ``` or ``` ... ```).
        for prefix in ("```json", "```javascript", "```"):
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix) :].strip()
                break
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

        # If extra prose is present, keep only the outermost JSON object.
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and start < end:
            cleaned = cleaned[start : end + 1]

        try:
            return json.loads(cleaned)
        except Exception as exc:
            print("Failed to parse generated query:", exc)
            return {}

    def execute_query_object(self, query_object: dict) -> dict:
        """Execute a provided OpenSearch query object and return results.
        This method allows executing a fully formed OpenSearch query object,
        which can be useful for advanced users who want to run custom queries that
        may not be generated by the LLM. The query_object should be a valid
        OpenSearch query body (DSL). The method will execute the query against the
        specified index and return the search results.

        Args:
            query_object (dict): A valid OpenSearch query body (DSL) to execute.
        Returns:
            dict: The search results returned by OpenSearch.
        """

        if not isinstance(query_object, dict):
            return {}

        es = self._client.get_client()

        # Execute exactly what the caller provided; do not override size or
        # add/removes fields. This keeps the body identical to the generated
        # advanced query.
        return es.search(index=self._index, body=query_object)
