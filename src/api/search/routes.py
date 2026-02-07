from fastapi import APIRouter, Depends, Query, Request

from src.services.an_najah_repository_search_service import (
    AnNajahRepositorySearchService,
)

from .models import (
    AnswerRequest,
    AnswerResponse,
    GenerateQueryRequest,
    GenerateQueryResponse,
    SearchRequest,
    SearchResponse,
    SuggestResponse,
)
from .responses import (
    answer_responses,
    generate_query_responses,
    search_responses,
    suggest_responses,
)

router = APIRouter(prefix="/api")


def get_search_service(request: Request) -> AnNajahRepositorySearchService:
    """Dependency to get the AnNajahRepositorySearchService from the app state."""
    return request.app.state.search_service


@router.get("/suggest", **suggest_responses)
def suggest(
    q: str = Query(..., min_length=3),
    limit: int = Query(8, ge=1, le=20),
    service: AnNajahRepositorySearchService = Depends(get_search_service),
) -> SuggestResponse:
    """Endpoint to get autocomplete suggestions."""
    suggestions = service.suggest(prefix=q, limit=limit)
    return SuggestResponse(suggestions=suggestions)


@router.post("/search", **search_responses)
def search(
    request: SearchRequest,
    service: AnNajahRepositorySearchService = Depends(get_search_service),
) -> SearchResponse:
    """Endpoint to execute a custom search."""
    results = service.search_using_query(query=request.query)
    return SearchResponse(results=results)


@router.post("/generate-query", **generate_query_responses)
def generate_query(
    request: GenerateQueryRequest,
    service: AnNajahRepositorySearchService = Depends(get_search_service),
) -> GenerateQueryResponse:
    """Endpoint to generate a search query from a user natural language prompt."""
    results, generated_query = service.generate_query(request.prompt)
    return GenerateQueryResponse(results=results, generated_query=generated_query)


@router.post("/answer", **answer_responses)
def answer(
    request: AnswerRequest,
    service: AnNajahRepositorySearchService = Depends(get_search_service),
) -> AnswerResponse:
    """Endpoint to generate an answer using the RAG pipeline."""
    answer_text, sources = service.generate_answer(request.query)
    return AnswerResponse(answer=answer_text, sources=sources)
