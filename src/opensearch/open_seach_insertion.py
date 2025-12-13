import json
from pathlib import Path
import re
import html
from bs4 import BeautifulSoup  

from extracters.abstract_classes.abc_extractor import ABCExtractor
from opensearch.abstract_classes.search_insertion import ABCSearchInsertion
from opensearch.mapping import ProjectMapping


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
        
    def sanitize_text(raw: str) -> str:
        """Minimal cleaning before embedding: strip HTML, unescape entities,
        remove control characters, collapse whitespace. Keep stopwords and natural grammar."""
        if not raw:
            return ""

        # 1) Remove script/style blocks & tags using BeautifulSoup
        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        text = soup.get_text(separator=" ")

        # 2) Unescape HTML entities
        text = html.unescape(text)

        # 3) Remove non-printable/control characters
        text = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", text)

        # 4) Optionally remove long code blocks fenced by backticks (common in scraped HTML)
        # Keep this if you frequently index pages with code you don't want embedded.
        text = re.sub(r"```[\s\S]*?```", " ", text)
        text = re.sub(r"`[^`]{30,}`", " ", text)  # single-line long inline code

        # 5) Collapse repeated whitespace/newlines to single spaces
        text = re.sub(r"\s+", " ", text).strip()


        return text


    def extract_and_insert(
        self,
        index_name: str | None = None,
        jsonl_path: str = "scraped_data/bulk_opensearch.jsonl",
    ):
        """Read documents from a JSONL file and insert them into OpenSearch.

        This uses the ``ProjectMapping`` instance to ensure the index is
        created with the correct mappings and to compute the knn vector
        for the abstract text.
        """

        if index_name is None:
            index_name = self.index_name

        jsonl_file = Path(jsonl_path)
        if not jsonl_file.exists():
            raise FileNotFoundError(f"JSONL file not found: {jsonl_file}")

        # Ensure index exists with the configured mappings/settings
        self.project_mapping.create_index(index_name)

        with jsonl_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    doc = json.loads(line)
                except json.JSONDecodeError:
                    # Skip malformed lines but continue processing the rest
                    continue

                # Compute embedding for the abstract fields
                abstract = doc.get("abstract", {}) or {}
                abstract_en = " ".join(abstract.get("en", []) or [])
                abstract_ar = " ".join(abstract.get("ar", []) or [])
                text_for_embedding = " ".join(
                    part for part in [abstract_en, abstract_ar] if part
                )

                if text_for_embedding:
                    vector = self.project_mapping.encode_text(text_for_embedding)
                    doc["abstract_vector"] = vector.tolist()

                # Optionally, temporal/location extractors could be applied here
                # to enrich the document further before indexing.

                self.opensearch_client.index(index=index_name, body=doc)
