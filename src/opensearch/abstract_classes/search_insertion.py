from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable


class AbstractDocumentIngestionService(ABC):
    """Contract for services that transform raw records and ingest them into search."""

    @abstractmethod
    def stream_documents(
        self,
        *,
        index_name: str,
        jsonl_path: str,
    ) -> Iterable[Dict[str, Any]]:
        """Yield search documents ready for bulk indexing."""

    @abstractmethod
    def ingest(
        self,
        *,
        index_name: str | None = None,
        jsonl_path: str | None = None,
    ) -> None:
        """Perform ingestion using the configured search backend."""
