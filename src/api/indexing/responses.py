from .models import IndexResponse

index_responses = {
    "response_model": IndexResponse,
    "summary": "Index repository documents",
    "description": "Run the indexing pipeline over a JSONL file and insert into OpenSearch.",
    "responses": {
        400: {"description": "Invalid indexing request."},
        500: {"description": "Internal server error."},
    },
    "tags": ["indexing"],
}
