from abc import ABC, abstractmethod
class ABCExtractor(ABC):
    @abstractmethod
    def extract(self, text, lang):
        """
        Extract relevant information from the given text.
        
        args:
            text (str): The input text to extract information from.
            lang (str): The language of the input text.
            
        returns:
            set: A set of extracted information.
        """
        pass
    def _validate_text(self, text):
        """
        Validate a given text

        Args:
            text (str): The input text to validate.

        Raises:
            ValueError: If the text is not a non-empty string.
        """
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Input text must be a non-empty string.")