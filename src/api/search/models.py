from typing import Any, Dict, List

from pydantic import BaseModel, Field


class SuggestResponse(BaseModel):
    """Response model for autocomplete suggestions."""

    suggestions: List[str] = Field(default_factory=list)


class AnswerRequest(BaseModel):
    """Request model for generating an answer."""

    query: str
    size: int = Field(default=5, ge=1, le=10)
    history: list[dict] | None = None


class DocumentSource(BaseModel):
    """Cited document metadata returned with an answer."""

    item_uuid: str | None = None
    title: str
    snippet: str | None = None


class AnswerResponse(BaseModel):
    """Response model for generated answers."""

    answer: str
    sources: List[DocumentSource] = Field(default_factory=list)


class GenerateQueryRequest(BaseModel):
    """Request model for generating a query."""

    prompt: str
    size: int = Field(default=30, ge=1, le=100)


class GenerateQueryResponse(BaseModel):
    """Response model for generated queries."""

    results: Dict[str, Any]
    generated_query: Any


class SearchRequest(BaseModel):
    """Request model for executing a search."""

    query: Dict[str, Any]


class SearchResponse(BaseModel):
    """Response model for search results."""

    results: Dict[str, Any]


class UserQueryRequest(BaseModel):
    """Request model for building a user query DSL."""

    query: str


class UserQueryResponse(BaseModel):
    """Response model for user query DSL."""

    dsl: Dict[str, Any]
