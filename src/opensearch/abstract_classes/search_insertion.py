from abc import ABC, abstractmethod
from typing import Any


class ABCSearchInsertion(ABC):
    """
    An abstract base class for search insertion operations.
    so that any subclass must implement the extract_and_insert method.
    so if the user wants to change the extraction or insertion logic, or
    the service like switching from OpenSearch to another search engine,
    they can do so by creating a new subclass that implements this method.

    Args:
        ABC (_type_): _description_

    Raises:
        NotImplementedError: _description_
    """

    @abstractmethod
    def extract_and_insert(
        self,
        index_name: str,
        jsonl_path: str = "scraped_data/bulk_opensearch.jsonl",
    ) -> Any:
        """Insert documents from a JSONL file into an OpenSearch index.

        Implementations should read JSON objects line-by-line from the
        provided file, apply any required extraction/augmentation logic,
        and index the resulting documents into the given index.
        """

        raise NotImplementedError
