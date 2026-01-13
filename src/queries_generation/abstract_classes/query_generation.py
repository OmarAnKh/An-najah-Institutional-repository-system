from abc import ABC, abstractmethod

# Define an abstract class for query generation
class ABCQueryGeneration(ABC):
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