import json
from pathlib import Path
import re
import html
from bs4 import BeautifulSoup  
from langdetect import detect
from itertools import zip_longest

from src.extracters.abstract_classes.abc_extractor import ABCExtractor
from src.opensearch.abstract_classes.search_insertion import ABCSearchInsertion
from src.extracters.abstract_classes.abc_geo_location_finder import ABCGeoLocationFinder
from src.opensearch.mapping import ProjectMapping
from dtos.article_dto import ArticleDTO 
from dtos.localized_text import LocalizedText
from dtos.localized_vector import LocalizedVector
from dtos.geo_coordinates import GeoCoordinates
from dtos.geo_reference import GeoReference


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
            index_name: Name of the OpenSearch index to insert into.
        """

        self.project_mapping = project_mapping
        self.opensearch_client = project_mapping.client
        self.location_extractor: ABCExtractor = location_extractor
        self.temporal_extractor: ABCExtractor = temporal_extractor
        self.geo_location_finder: ABCGeoLocationFinder = geo_location_finder
        self.index_name = index_name
        
    def sanitize_text(self, raw: str) -> str:
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
    
    def process_dict(self ,obj: dict) -> LocalizedText:
        temp = dict()
        for value in obj.values():
            if (len(value) > 0) and (isinstance(value[0], str)):
                clean_text = self.sanitize_text(value[0])
                lang = detect(clean_text)
                temp[lang] = clean_text
        
        return LocalizedText(**temp)
    
    def extract_temporal_expressions(self ,text : str, lang: str) -> list[str]:
        """Extract temporal expressions from text using the temporal extractor."""
        result = self.temporal_extractor.extract(text=text, lang=lang)
        return list(result) if result else []
    
    def extract_geo_references(self ,text: str, lang: str) -> list[str]:
        """Extract geo references from text using the location extractor."""
        result = self.location_extractor.extract(text=text, lang=lang)
        return list(result) if result else []

    def get_coordinates(self ,place_name: str) -> GeoCoordinates | None:
        """Get coordinates for a place name using the geo location finder."""
        geo_ref = self.geo_location_finder._geocode_single_place(place_name)
        if geo_ref and geo_ref.coordinates:
            return GeoCoordinates(
                lat=geo_ref.coordinates.lat,
                lon=geo_ref.coordinates.lon,
            )
        return None
    
    def get_geo_points(self ,place_names: list[str]) -> list[GeoReference]:
        """Get geo points for a list of place names using the geo location finder."""
        geo_refs = self.geo_location_finder.extract_from_places(place_names)
        return geo_refs
    
    def encode_text(self ,text: str) -> list[float]:
        """Encode text using the project mapping's model."""
        vector = self.project_mapping.encode_text(text)
        return vector.tolist() if hasattr(vector, "tolist") else list(vector)
    

    def indexing_pipeline(self ,obj: dict) -> list[ArticleDTO]:
        """Full preprocessing pipeline for dict before embedding text."""
        # title 
        title_dto = self.process_dict(obj["title"])
        
        # abstract
        abstract_dict = self.process_dict(obj["abstract"])
        
        # temporal expressions
        en_temporal_expressions = self.extract_temporal_expressions(text=abstract_dict.en or "", lang="en")
        ar_temporal_expressions = self.extract_temporal_expressions(text=abstract_dict.ar or "", lang="ar")
        temporal_expressions = list(set(en_temporal_expressions + ar_temporal_expressions))
        # temporal_expressions = self.extract_temporal_expressions(abstract_dict)
        
        # geo references
        en_geo_references = self.extract_geo_references(text=abstract_dict.en or "", lang="en")
        ar_geo_references = self.extract_geo_references(text=abstract_dict.ar or "", lang="ar")
        geo_locations = list(set(en_geo_references + ar_geo_references))
        
        geo_references = self.get_geo_points(geo_locations)
        
        # chunks
        en_chunks = self.project_mapping.chunk_text(abstract_dict.en, max_tokens=450, overlap=50)
        ar_chunks = self.project_mapping.chunk_text(abstract_dict.ar, max_tokens=450, overlap=50)
        
        combined_chunks = [LocalizedText(en=x, ar=y) for x, y in zip_longest(en_chunks, ar_chunks, fillvalue=None)]
        
        docs = []
        
        # embedding 
        for chunk_id, chunk in enumerate(combined_chunks):
            abstract_vector = LocalizedText(
                en=self.encode_text(chunk.en) if chunk.en else None,
                ar=self.encode_text(chunk.ar) if chunk.ar else None,
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
                publicationDate=obj.get("publicationDate", None),
                geoReferences=geo_references,
                temporalExpressions=temporal_expressions,
            )
            
            docs.append(article_dto)
        
        return docs
            
        

    # def preproccesing(
    #     self,
    #     jsonl_path: str = "scraped_data/bulk_opensearch.jsonl",
    # ):
    #     """placeholder for preproccesing function"""

    #     jsonl_file = Path(jsonl_path)
    #     if not jsonl_file.exists():
    #         raise FileNotFoundError(f"JSONL file not found: {jsonl_file}")

    #     # Ensure index exists with the configured mappings/settings
    #     self.project_mapping.create_index(self.index_name)

    #     with jsonl_file.open("r", encoding="utf-8") as f:
    #         for line in f:
    #             line = line.strip()
    #             if not line:
    #                 continue

    #             try:
    #                 json.loads(line)
    #             except json.JSONDecodeError:
    #                 # Skip malformed lines but continue processing the rest
    #                 continue

    #             # Compute embedding for the abstract fields
    #             # abstract = doc.get("abstract", {}) or {}
    #             # abstract_en = " ".join(abstract.get("en", []) or [])
    #             # abstract_ar = " ".join(abstract.get("ar", []) or [])

    def extract_and_insert(
        self,
    ):
        """placeholder for extract_and_insert function"""
        # self.opensearch_client.index(index=index_name, body=doc)
        pass
