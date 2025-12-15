from pydantic import BaseModel, Field


class LocalizedVector(BaseModel):
    """A DTO for localized vector representations."""

    en: list[float] = Field(default_factory=list)
    ar: list[float] = Field(default_factory=list)
