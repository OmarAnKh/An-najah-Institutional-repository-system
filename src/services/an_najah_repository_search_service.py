from src.opensearch.abstract_classes.ABC_client import ABCClient
from src.query_utils.suggest_query import build_suggest_query
from src.query_utils.query_preprocessor import prepare_input
from src.query_utils.full_text_query import build_hybrid_query_pipeline


class AnNajahRepositorySearchService:
    """
    Service for indexing and searching articles in OpenSearch.
    """

    def __init__(
        self,
        index: str,
        client: ABCClient,
    ):
        """
            Class constructor inject the required dependencies via the parameters
        Args:
            index (str): The name of the index to operate on.
            client (ABCClient): An instance of ABCClient to interact with OpenSearch.
        """
        self._client = client
        self._index = index

    def search_articles(self, query: dict):
        """simple search function for custom queries

        Args:
            query (dict): The search query as a dictionary.

        Returns:
            dict: The search results.
        """
        es = self._client.get_client()
        return es.search(index=self._index, body=query)

    def client_health(self):
        """Check the health of the OpenSearch client."""
        es = self._client.get_client()
        return es.cluster.health()

    def suggest(self, prefix: str, limit: int = 8) -> list[str]:
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
        lang, lexical25_clean_query, semantic_vector_query, temporals, geo_refs = (prepare_input(q))

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
