from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field

from src.dtos.geo_reference import GeoReference
from src.dtos.localized_text import LocalizedText
from src.dtos.localized_vector import LocalizedVector


class ArticleDTO(BaseModel):
    """A DTO for articles to be indexed in OpenSearch."""

    collection: str = ""
    bitstream_uuid: str = ""
    chunk_id: int

    title: Optional[LocalizedText] = None
    abstract: Optional[LocalizedText] = None
    abstract_vector: Optional[LocalizedVector] = None

    author: List[str] = Field(default_factory=list)
    hasFiles: bool = False
    publicationDate: Optional[date] = None
    geoReferences: List[GeoReference] = Field(default_factory=list)
    temporalExpressions: List[str] = Field(default_factory=list)
