from pydantic import BaseModel

class LocalizedVector(BaseModel):
    en: list[float] = []
    ar: list[float] = []