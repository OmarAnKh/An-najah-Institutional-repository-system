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
    UserQueryRequest,
    UserQueryResponse,
)
from .responses import (
    answer_responses,
    generate_query_responses,
    search_responses,
    suggest_responses,
    user_query_responses,
)

router = APIRouter(prefix="/api")


def get_search_service(request: Request) -> AnNajahRepositorySearchService:
    return request.app.state.search_service


@router.get("/suggest", **suggest_responses)
def suggest(
    q: str = Query(..., min_length=3),
    limit: int = Query(8, ge=1, le=20),
    service: AnNajahRepositorySearchService = Depends(get_search_service),
) -> SuggestResponse:
    suggestions = service.suggest(prefix=q, limit=limit)
    return SuggestResponse(suggestions=suggestions)


@router.post("/search", **search_responses)
def search(
    request: SearchRequest,
    service: AnNajahRepositorySearchService = Depends(get_search_service),
) -> SearchResponse:
    results = service.search_articles(query=request.query)
    return SearchResponse(results=results)


@router.post("/generate-query", **generate_query_responses)
def generate_query(
    request: GenerateQueryRequest,
    service: AnNajahRepositorySearchService = Depends(get_search_service),
) -> GenerateQueryResponse:
    results, generated_query = service.generate_query(request.prompt)
    return GenerateQueryResponse(results=results, generated_query=generated_query)


@router.post("/user-query", **user_query_responses)
def user_query(
    request: UserQueryRequest,
    service: AnNajahRepositorySearchService = Depends(get_search_service),
) -> UserQueryResponse:
    dsl = service.user_query(request.query)
    return UserQueryResponse(dsl=dsl)


@router.post("/answer", **answer_responses)
def answer(
    request: AnswerRequest,
    service: AnNajahRepositorySearchService = Depends(get_search_service),
) -> AnswerResponse:
    answer_text = service.generate_answer(request.query)
    return AnswerResponse(answer=answer_text)
