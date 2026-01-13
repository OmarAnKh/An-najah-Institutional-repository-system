from fastapi import APIRouter, Depends, Request

from src.services.open_seach_insertion import OpenSearchInsertion

from .models import IndexRequest, IndexResponse
from .responses import index_responses

router = APIRouter(prefix="/api")


def get_insertion_service(request: Request) -> OpenSearchInsertion:
    return request.app.state.insertion_service


@router.post("/index", **index_responses)
def index(
    request: IndexRequest,
    service: OpenSearchInsertion = Depends(get_insertion_service),
) -> IndexResponse:
    result = service.extract_and_insert(
        chunk_size=request.chunk_size,
        jsonl_path=request.jsonl_path,
    )
    return IndexResponse(**result)
