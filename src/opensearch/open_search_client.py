from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from .abstract_classes import ABCClient
from global_config import global_config
import boto3


class OpenSearchClient(ABCClient):
    _instance = None
    _client: OpenSearch | None = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, use_ssl: bool = True, verify_certs: bool = True):
        if self.__class__._initialized:
            return

        # Note: AWS IAM usually requires SSL to be True
        self.use_ssl = use_ssl
        self.verify_certs = verify_certs
        self.__class__._initialized = True

    # In src/opensearch/open_search_client.py
    def get_client(self) -> OpenSearch:
        if self.__class__._client is None:

            session = boto3.Session()

            sts = session.client("sts")
            print("STS identity:", sts.get_caller_identity())

            credentials = session.get_credentials()
            region = global_config.aws_region
            service = "es"

            awsauth = AWS4Auth(
                credentials.access_key,
                credentials.secret_key,
                region,
                service,
                session_token=credentials.token,
            )

            self.__class__._client = OpenSearch(
                hosts=[
                    {
                        "host": global_config.opensearch_host,
                        "port": global_config.opensearch_port,
                    }
                ],
                http_auth=awsauth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
            )

        return self.__class__._client
