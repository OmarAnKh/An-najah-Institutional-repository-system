from opensearchpy import OpenSearch
from abc import ABC, abstractmethod


class ABCClient(ABC):
    """Abstract base class for OpenSearch clients."""

    @abstractmethod
    def get_client(self) -> OpenSearch:
        """Return an instance of the OpenSearch client."""
        raise NotImplementedError
