from typing import Optional
from pydantic import BaseModel

from dtos.geo_coordinates import GeoCoordinates


class GeoReference(BaseModel):
    """A DTO for geographical references."""

    placeName: str
    coordinates: Optional[GeoCoordinates] = None
