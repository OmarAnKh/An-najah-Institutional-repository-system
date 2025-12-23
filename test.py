import time
import requests
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion
from prompt_toolkit.key_binding import KeyBindings
from src.services.an_najah_repository_search_service import (
    AnNajahRepositorySearchService,
)
from src.opensearch.open_search_client import OpenSearchClient
from src.queries_generation.query_generation import QueryGeneration
from src.opensearch.mapping import ProjectMapping


from global_config import global_config


class RemoteAutoSuggest(AutoSuggest):
    """
    Fish-shell inline suggestion:
    Show the remainder of the best suggestion as ghost text.
    """

    def __init__(self, min_chars=3, ttl_seconds=0.6, timeout=0.25):
        self.min_chars = min_chars
        self.ttl_seconds = ttl_seconds
        self.timeout = timeout
        self._cache = {}  # prefix -> (timestamp, suggestions)

    def _fetch(self, prefix: str):
        now = time.time()
        cached = self._cache.get(prefix)
        if cached and (now - cached[0]) < self.ttl_seconds:
            return cached[1]

        try:
            r = requests.get(
                global_config.suggest_url,
                params={"q": prefix, "limit": 10},
                timeout=self.timeout,
            )
            r.raise_for_status()
            suggestions = r.json()
            if not isinstance(suggestions, list):
                suggestions = []
        except Exception:
            suggestions = []

        self._cache[prefix] = (now, suggestions)
        return suggestions

    def get_suggestion(self, buffer, document):
        typed = (document.text or "").strip()
        if len(typed) < self.min_chars:
            return None

        suggestions = self._fetch(typed)

        # pick first suggestion that starts with typed text (case-insensitive)
        low = typed.lower()
        for s in suggestions:
            if isinstance(s, str) and s.lower().startswith(low) and len(s) > len(typed):
                remainder = s[len(typed) :]
                return Suggestion(remainder)

        return None


query_generation = QueryGeneration(ollama_model=global_config.generative_model_name)

client = OpenSearchClient(True, True)
print("OpenSearch client initialized.")

project_mapping = ProjectMapping(
    model_name=global_config.embedding_model_name,
    opensearch_client=client,
)

opensearch_search_service = AnNajahRepositorySearchService(
    index=global_config.index_name,
    client=client,
    mapping=project_mapping,
    query_generator=query_generation,
)


def main():
    kb = KeyBindings()

    # Accept ghost suggestion with TAB (Right arrow works by default too)
    @kb.add("tab")
    def _(event):
        b = event.app.current_buffer
        if b.suggestion:
            b.insert_text(b.suggestion.text)

    session = PromptSession(auto_suggest=RemoteAutoSuggest(), key_bindings=kb)

    while True:
        user_text = session.prompt("Search> ")
        if user_text.lower() in ("exit", "quit"):
            break

        user_query = opensearch_search_service.user_query(user_text)
        res = opensearch_search_service.search_articles(user_query)
        hits = res.get("hits", {}).get("hits", [])
        print(f"Found {len(hits)} results:")

        for i, hit in enumerate(hits, start=1):
            src = hit.get("_source", {}) or {}

            title = (src.get("title", {}) or {}).get("en") or "No Title"
            abstract = (src.get("abstract", {}) or {}).get("en") or "No Abstract"

            print(f"{i}. {title}")
            print(f"   Abstract: {abstract}\n")


if __name__ == "__main__":
    main()
