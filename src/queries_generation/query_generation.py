import ollama
from abc import ABC, abstractmethod
from prompts import query_generation_prompt
import json


# Define an abstract class for query generation
class Query(ABC):
    """
    Abstract base class for generating search queries.

    This class defines the structure that all query generation classes must follow.
    Any class that inherits from `Query` must implement the `generate_opensearch_query`
    method to define how to generate a specific type of search query.

    Methods:
    --------
    generate_opensearch_query(user_prompt: str) -> str:
        Abstract method that generates a search query based on the user's prompt.
    """

    @abstractmethod
    def generate_opensearch_query(self, user_prompt: str, mapping):
        """
        Abstract method to generate a search query.

        This method must be implemented by any subclass. It defines the logic for
        generating a search query based on the user prompt.

        Parameters:
        -----------
        user_prompt : str
            The user's input or query for generating the search.

        Returns:
        --------
        str
            A query string that can be used to search a system (e.g., OpenSearch).
        """
        pass


# Implement the abstract class in the concrete class
class QueryGeneration(Query):
    """
    Concrete implementation of the `Query` class that generates a search query
    using an external model (e.g., Ollama's Llama2) and a user prompt.

    This class generates an OpenSearch query based on the user's input,
    by interacting with an Ollama model for natural language processing.

    Attributes:
    -----------
    client : ollama.Client
        The Ollama client used to interact with the language model.

    model : str
        The model name to be used for generating responses (default: "llama2:latest").

    Methods:
    --------
    generate_opensearch_query(user_prompt: str) -> str:
        Generates an OpenSearch query based on the given user prompt.
    """

    def __init__(self, ollama_model: str):
        """
        Initializes the `QueryGeneration` object by setting up the Ollama client
        and selecting the model for query generation.

        The model name is set to "llama3.1:8b" by default.
        """
        # Initialize the Ollama client
        self.client = ollama.Client()
        self.model = ollama_model

    def generate_opensearch_query(self, user_prompt: str, mapping):
        """
        Generates an OpenSearch query by sending the user's prompt to the Ollama model
        and retrieving a natural language response.

        Parameters:
        -----------
        user_prompt : str
            The input provided by the user, which will be used to generate a query.

        Returns:
        --------
        str
            The generated OpenSearch query as a string.
        """
        # Combine system and user messages
        system_part = (
            query_generation_prompt
            + "\n\nINDEX MAPPING:\n"
            + json.dumps(mapping, ensure_ascii=False)
        )
        combined_prompt = f"System: {system_part}\nUser: {user_prompt}\nAssistant:"

        response = self.client.generate(model=self.model, prompt=combined_prompt)
        return response.response
