from abc import ABC, abstractmethod


class ABCGenerativeModel(ABC):
    """
    Abstract base class for generative models. Defines the interface for generating responses
    based on input queries and retrieved documents.
    """

    @abstractmethod
    def generate(self, query: str, documents: list[str]) -> str:
        """
        Generate a response based on the input query and retrieved documents.

        Args:
            query (str): The input query string.
            documents (list): A list of retrieved documents.
        Returns:
            str: The generated response.
        """
        pass

    @abstractmethod
    def _add_to_history(self, query: str, response: str) -> None:
        """
        Save the query and response to history.

        Args:
            query (str): The input query string.
            response (str): The generated response.
        """
        pass

    @abstractmethod
    def formulate_query(self, user_input: str) -> str:
        """
        Formulate a query based on user input.

        Args:
            user_input (str): The user's input string.

        Returns:
            str: The formulated query.
        """
        pass
