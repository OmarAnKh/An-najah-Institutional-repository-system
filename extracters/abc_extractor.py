from abc import ABC, abstractmethod
class ABCExtractor(ABC):
    @abstractmethod
    def extract(self, text, lang):
        pass
    def _validate_text(self, text):
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Input text must be a non-empty string.")