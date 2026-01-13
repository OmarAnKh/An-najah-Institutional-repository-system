from typing import Any, Dict, List

from pydantic import BaseModel, Field


class SuggestResponse(BaseModel):
    """Response model for autocomplete suggestions."""

    suggestions: List[str] = Field(default_factory=list)


class AnswerRequest(BaseModel):
    """Request model for generating an answer."""

    query: str


class AnswerResponse(BaseModel):
    """Response model for generated answers."""

    answer: str


class GenerateQueryRequest(BaseModel):
    """Request model for generating a query."""

    prompt: str


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
