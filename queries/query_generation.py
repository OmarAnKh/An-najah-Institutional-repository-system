import ollama
from prompt import prompt_function
from abc import ABC, abstractmethod


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
    def generate_opensearch_query(self, user_prompt: str):
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

    def __init__(self):
        """
        Initializes the `QueryGeneration` object by setting up the Ollama client
        and selecting the model for query generation.

        The model name is set to "llama2:latest" by default.
        """
        # Initialize the Ollama client
        self.client = ollama.Client()
        self.model = "llama2:latest"

    def generate_opensearch_query(self, user_prompt: str):
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
        combined_prompt = f"System: {prompt_function()}\nUser: {user_prompt}\nAssistant:"

        # Send the combined prompt to the Ollama model for query generation
        response = self.client.generate(
            model=self.model,
            prompt=combined_prompt
        )

        return response.response


# Usage
query_generator = QueryGeneration()
prompt = "give me all the documents from 2018"
result = query_generator.generate_opensearch_query(prompt)

print("Response from Ollama:")
print(result)
