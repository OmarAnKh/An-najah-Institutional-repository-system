from typing import Optional
from pydantic import BaseModel


class LocalizedText(BaseModel):
    """A DTO for localized text representations."""

    en: Optional[str] = None
    ar: Optional[str] = None
