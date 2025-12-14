from pydantic import BaseModel

class GeoCoordinates(BaseModel):
    lat: float
    lon: float