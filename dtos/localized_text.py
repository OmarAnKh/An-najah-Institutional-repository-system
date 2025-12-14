from typing import Optional
from pydantic import BaseModel


class LocalizedText(BaseModel):
    en: Optional[str] = None
    ar: Optional[str] = None