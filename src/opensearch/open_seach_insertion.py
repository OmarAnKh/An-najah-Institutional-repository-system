import json
from pathlib import Path

from src.extracters.abstract_classes.abc_extractor import ABCExtractor
from src.opensearch.abstract_classes.search_insertion import ABCSearchInsertion
from src.opensearch.mapping import ProjectMapping


class OpenSearchInsertion(ABCSearchInsertion):
    """Insert repository documents into OpenSearch using configured mappings.

    This class ties together the OpenSearch mapping configuration, the
    sentence-transformer model (via ``ProjectMapping``), and the optional
    location/temporal extractors used to enrich documents before indexing.
    """

    def __init__(
        self,
        project_mapping: ProjectMapping,
        location_extractor: ABCExtractor,
        temporal_extractor: ABCExtractor,
        index_name: str,
    ):
        """Create an insertion helper bound to a specific index.

        Args:
            project_mapping: Mapping/encoding helper that owns the
                OpenSearch client and model.
            location_extractor: Extractor used to derive location data
                from document text, if desired.
            temporal_extractor: Extractor used to derive temporal
                expressions from document text, if desired.
            index_name: Name of the OpenSearch index to insert into.
        """

        self.project_mapping = project_mapping
        self.opensearch_client = project_mapping.client
        self.location_extractor: ABCExtractor = location_extractor
        self.temporal_extractor: ABCExtractor = temporal_extractor
        self.index_name = index_name

    def preproccesing(
        self,
        jsonl_path: str = "scraped_data/bulk_opensearch.jsonl",
    ):
        """placeholder for preproccesing function"""

        jsonl_file = Path(jsonl_path)
        if not jsonl_file.exists():
            raise FileNotFoundError(f"JSONL file not found: {jsonl_file}")

        # Ensure index exists with the configured mappings/settings
        self.project_mapping.create_index(self.index_name)

        with jsonl_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    json.loads(line)
                except json.JSONDecodeError:
                    # Skip malformed lines but continue processing the rest
                    continue

                # Compute embedding for the abstract fields
                # abstract = doc.get("abstract", {}) or {}
                # abstract_en = " ".join(abstract.get("en", []) or [])
                # abstract_ar = " ".join(abstract.get("ar", []) or [])

    def extract_and_insert(
        self,
    ):
        """placeholder for extract_and_insert function"""
        # self.opensearch_client.index(index=index_name, body=doc)
        pass
