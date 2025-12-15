import html
import json
import re
from datetime import date
from itertools import zip_longest
from typing import Any

from bs4 import BeautifulSoup
from langdetect import LangDetectException, detect
from opensearchpy import helpers

from src.extracters.abstract_classes.abc_extractor import ABCExtractor
from src.extracters.abstract_classes.abc_geo_location_finder import ABCGeoLocationFinder
from src.opensearch.mapping import ProjectMapping
from src.dtos.article_dto import ArticleDTO
from src.dtos.localized_text import LocalizedText
from src.dtos.localized_vector import LocalizedVector
from src.dtos.geo_coordinates import GeoCoordinates
from src.dtos.geo_reference import GeoReference


class OpenSearchInsertion:
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
        geo_location_finder: ABCGeoLocationFinder,
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
            geo_location_finder: Geolocation finder to get coordinates
                for extracted location names.
            index_name: Name of the OpenSearch index to insert into.
        """

        self.project_mapping = project_mapping
        self.opensearch_client = project_mapping.client
        self.location_extractor: ABCExtractor = location_extractor
        self.temporal_extractor: ABCExtractor = temporal_extractor
        self.geo_location_finder: ABCGeoLocationFinder = geo_location_finder
        self.index_name = index_name
        self.project_mapping.create_index(index_name)

    def sanitize_text(self, raw: str) -> str:
        """Minimal cleaning before embedding: strip HTML, unescape entities,
        remove control characters, collapse whitespace. Keep stopwords and natural grammar.
        args:
            raw (str): Raw HTML/text input
        returns:
            str: Cleaned text
        """
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

    def process_dict(self, obj: dict) -> LocalizedText:
        """Process a dict with localized text fields into LocalizedText DTO.
        1) Sanitize each text entry
        2) Detect language
        Args:
            obj (dict): _raw localized text dictionary_
        Returns:
            LocalizedText: _processed localized text DTO_
        """
        detected: dict[str, str] = {}
        for value in obj.values():
            if not value or not isinstance(value[0], str):
                continue

            clean_text = self.sanitize_text(value[0])
            if not clean_text:
                continue

            try:
                lang = detect(clean_text)
            except LangDetectException:
                continue

            if lang not in {"en", "ar"}:
                continue

            detected[lang] = clean_text

        return LocalizedText(**detected)

    def extract_temporal_expressions(self, text: str, lang: str) -> list[str]:
        """Extract temporal expressions from text using the temporal extractor.
        args:
            text (str): Input text
            lang (str): Language code ("en" or "ar")
        returns:
            list[str]: List of extracted temporal expressions
        """
        result = self.temporal_extractor.extract(text=text, lang=lang)
        return list(result) if result else []

    def extract_geo_references(self, text: str, lang: str) -> list[str]:
        """Extract geo references from text using the location extractor.
        args:
            text (str): Input text
            lang (str): Language code ("en" or "ar")
        returns:
            list[str]: List of extracted geo references
        """
        result = self.location_extractor.extract(text=text, lang=lang)
        return list(result) if result else []

    def get_coordinates(self, place_name: str) -> GeoCoordinates | None:
        """Get coordinates for a place name using the geo location finder.
        args:
            place_name (str): Name of the place
            returns:
            GeoCoordinates | None: Coordinates if found, else None
        """
        geo_ref = self.geo_location_finder._geocode_single_place(place_name)
        if geo_ref and geo_ref.coordinates:
            return GeoCoordinates(
                lat=geo_ref.coordinates.lat,
                lon=geo_ref.coordinates.lon,
            )
        return None

    def get_geo_points(self, place_names: list[str]) -> list[GeoReference]:
        """Get geo points for a list of place names using the geo location finder.
        args:
            place_names (list[str]): List of place names
            returns:
            list[GeoReference]: List of GeoReference DTOs
        """
        geo_refs = self.geo_location_finder.extract_from_places(place_names)
        return geo_refs

    def _parse_publication_date(self, value) -> date | None:
        """Normalize publicationDate to a date or None.

        - Accepts date directly.
        - If int or numeric string (year), converts to Jan 1 of that year.
        - If full ISO date string, lets pydantic coerce it later.
        - Otherwise returns None.
        """

        if value is None:
            return None

        if isinstance(value, date):
            return value

        # Year as int or numeric string
        if isinstance(value, int):
            return date(value, 1, 1)

        if isinstance(value, str):
            v = value.strip()
            if v.isdigit() and len(v) == 4:
                try:
                    return date(int(v), 1, 1)
                except ValueError:
                    return None
            # Leave other strings for pydantic to parse if valid ISO, else None
            return v or None

        return None

    def encode_text(self, text: str) -> list[float]:
        """Encode text using the project mapping's model.
        args:
            text (str): Input text
        returns:
            list[float]: Encoded vector as a list of floats
        """
        vector = self.project_mapping.encode_text(text)
        return vector.tolist() if hasattr(vector, "tolist") else list(vector)

    def indexing_pipeline(self, obj: dict) -> list[ArticleDTO]:
        """Full preprocessing pipeline for dict before embedding text.

        Args:
            obj (dict): _raw record dictionary_

        Returns:
            list[ArticleDTO]: _list of ArticleDTO chunks ready for indexing_
        """
        # title
        title_dto = self.process_dict(obj["title"])

        # abstract
        abstract_dict = self.process_dict(obj["abstract"])

        # temporal expressions
        en_temporal_expressions = self.extract_temporal_expressions(
            text=abstract_dict.en or "", lang="en"
        )
        ar_temporal_expressions = self.extract_temporal_expressions(
            text=abstract_dict.ar or "", lang="ar"
        )
        temporal_expressions = list(
            set(en_temporal_expressions + ar_temporal_expressions)
        )
        # temporal_expressions = self.extract_temporal_expressions(abstract_dict)

        # geo references
        en_geo_references = self.extract_geo_references(
            text=abstract_dict.en or "", lang="en"
        )
        ar_geo_references = self.extract_geo_references(
            text=abstract_dict.ar or "", lang="ar"
        )
        geo_locations = list(set(en_geo_references + ar_geo_references))

        geo_references = self.get_geo_points(geo_locations)

        # chunks
        en_chunks = self.project_mapping.chunk_text(
            abstract_dict.en or "", max_tokens=450, overlap=50
        )
        ar_chunks = self.project_mapping.chunk_text(
            abstract_dict.ar or "", max_tokens=450, overlap=50
        )

        combined_chunks = [
            LocalizedText(en=x, ar=y)
            for x, y in zip_longest(en_chunks, ar_chunks, fillvalue=None)
        ]

        docs = []

        # embedding
        for chunk_id, chunk in enumerate(combined_chunks):
            abstract_vector = LocalizedVector(
                en=self.encode_text(chunk.en) if chunk.en else [],
                ar=self.encode_text(chunk.ar) if chunk.ar else [],
            )

            article_dto = ArticleDTO(
                collection=obj.get("collection", ""),
                bitstream_uuid=obj.get("bitstream_uuid", ""),
                chunk_id=chunk_id,
                title=title_dto,
                abstract=chunk,
                abstract_vector=abstract_vector,
                author=obj.get("author", []),
                hasFiles=obj.get("hasFiles", False),
                publicationDate=self._parse_publication_date(
                    obj.get("publicationDate")
                ),
                geoReferences=geo_references,
                temporalExpressions=temporal_expressions,
            )

            docs.append(article_dto)

        return docs

    def generate_documents_from_json_stream(self, jsonl_path: str):
        """Generate documents from a JSON Lines file for bulk insertion.

        Each line is expected to be a standalone JSON object, not a single
        top-level JSON array. This avoids ijson's trailing-garbage errors on
        non-array payloads.
        """
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    # Skip malformed lines but continue processing the rest
                    continue
                if obj["abstract"]["en"] == [] and obj["abstract"]["ar"] == []:
                    continue
                dtos = self.indexing_pipeline(obj)  # returns list[ArticleDTO]
                for dto in dtos:
                    source = dto.model_dump()

                    # Drop empty or dimension-mismatched vectors to avoid KNN errors
                    vec = source.get("abstract_vector")
                    if vec is not None:
                        if (
                            not vec.get("en")
                            or len(vec.get("en", []))
                            != self.project_mapping.model_dimension
                        ):
                            vec.pop("en", None)
                        if (
                            not vec.get("ar")
                            or len(vec.get("ar", []))
                            != self.project_mapping.model_dimension
                        ):
                            vec.pop("ar", None)
                        if not vec:
                            source.pop("abstract_vector", None)

                    yield {
                        "_op_type": "index",
                        "_index": self.index_name,
                        "_id": f"{dto.bitstream_uuid}_{dto.chunk_id}",
                        "_source": source,
                    }

    def extract_and_insert(
        self,
        chunk_size: int = 500,
        jsonl_path: str = "scraped_data/bulk_opensearch.jsonl",
    ) -> Any:
        """Perform bulk insertion of documents from a JSON stream file.
        Args:
            file_path: Path to the JSON stream file containing raw records.
        """
        try:
            print("Starting bulk insertion...")
            documents = self.generate_documents_from_json_stream(jsonl_path)
            print("Generated documents for bulk insertion.")

            success, errors = helpers.bulk(
                self.opensearch_client,
                documents,
                chunk_size=chunk_size,
                raise_on_error=False,
                request_timeout=120,
            )

            if errors:
                print(
                    f"Bulk completed with {len(errors)} errors and {success} successes."
                )
                # Show a few sample errors to diagnose (avoid huge dumps)
                for err in errors[:5]:
                    print("Sample bulk error:", err)
            else:
                print(f"Bulk completed successfully. Indexed {success} documents.")

        except ImportError:
            print(
                "opensearchpy is not installed. Please install it to use bulk_insert."
            )
        except Exception as exc:
            print(f"Bulk ingestion failed: {exc}")
