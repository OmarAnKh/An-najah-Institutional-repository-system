from typing import Optional
from pydantic import BaseModel

from dtos.geo_coordinates import GeoCoordinates

class GeoReference(BaseModel):
    placeName: str
    coordinates: Optional[GeoCoordinates] = None