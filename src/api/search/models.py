from typing import Any, Dict, List

from pydantic import BaseModel, Field


class SuggestResponse(BaseModel):
    suggestions: List[str] = Field(default_factory=list)


class AnswerRequest(BaseModel):
    query: str


class AnswerResponse(BaseModel):
    answer: str


class GenerateQueryRequest(BaseModel):
    prompt: str


class GenerateQueryResponse(BaseModel):
    results: Dict[str, Any]
    generated_query: Any


class SearchRequest(BaseModel):
    query: Dict[str, Any]


class SearchResponse(BaseModel):
    results: Dict[str, Any]


class UserQueryRequest(BaseModel):
    query: str


class UserQueryResponse(BaseModel):
    dsl: Dict[str, Any]
