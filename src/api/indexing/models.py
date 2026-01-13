from typing import Optional

from pydantic import BaseModel, Field


class IndexRequest(BaseModel):
    jsonl_path: str = "scraped_data/bulk_opensearch.jsonl"
    chunk_size: int = Field(default=500, ge=1)


class IndexResponse(BaseModel):
    success: bool
    indexed: Optional[int] = None
    errors: Optional[int] = None
    message: str
