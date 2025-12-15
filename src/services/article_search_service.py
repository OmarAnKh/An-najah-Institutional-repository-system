from src.opensearch.abstract_classes.ABC_client import ABCClient


class ArticleSearchService:
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

    def index_article(self, id: str, body: dict):
        """
        Docstring for index_article

        param:
        index: the name of the index
        id: the document id
        body: the document body as a dictionary
        """
        es = self._client.get_client()
        es.index(index=self._index, id=id, body=body)

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
