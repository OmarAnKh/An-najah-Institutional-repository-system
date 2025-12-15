from pydantic import BaseModel


class GeoCoordinates(BaseModel):
    """A DTO for geographical coordinates."""

    lat: float
    lon: float
