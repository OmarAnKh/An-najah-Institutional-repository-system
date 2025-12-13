from opensearchpy import OpenSearch
from .abstract_classes import ABCClient
from global_config import global_config


class OpenSearchClient(ABCClient):
    """Singleton OpenSearch client using global configuration."""

    _instance = None
    _client: OpenSearch | None = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance of this class exists (singleton)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, use_ssl: bool = False, verify_certs: bool = True):
        """Store configuration once; actual client is created lazily."""
        if self.__class__._initialized:
            return

        self.use_ssl = use_ssl
        self.verify_certs = verify_certs
        self.__class__._initialized = True

    def get_client(self) -> OpenSearch:
        """Return the singleton OpenSearch client instance."""
        if self.__class__._client is None:
            self.__class__._client = OpenSearch(
                hosts=[
                    {
                        "host": global_config.opensearch_host,
                        "port": global_config.opensearch_port,
                    }
                ],
                http_auth=(
                    global_config.opensearch_username,
                    global_config.opensearch_password,
                ),
                use_ssl=self.use_ssl,
                verify_certs=self.verify_certs,
            )

        return self.__class__._client
