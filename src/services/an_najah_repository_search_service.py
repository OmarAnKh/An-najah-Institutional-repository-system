from src.opensearch.abstract_classes.ABC_client import ABCClient
from src.queries_generation.query_generation import QueryGeneration, Query
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
