from typing import Optional

from pydantic import BaseModel, Field


class IndexRequest(BaseModel):
    """Request model for indexing data into the search engine."""

    jsonl_path: str = "scraped_data/bulk_opensearch.jsonl"
    chunk_size: int = Field(default=500, ge=1)


class IndexResponse(BaseModel):
    """Response model for indexing operation results."""

    success: bool
    indexed: Optional[int] = None
    errors: Optional[int] = None
    message: str
