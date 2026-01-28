from .models import (
    AnswerResponse,
    GenerateQueryResponse,
    SearchResponse,
    SuggestResponse,
    UserQueryResponse,
)

suggest_responses = {
    "response_model": SuggestResponse,
    "summary": "Autocomplete suggestions",
    "description": "Return autocomplete suggestions for a query prefix.",
    "responses": {
        400: {"description": "Invalid query prefix."},
        500: {"description": "Internal server error."},
    },
    "tags": ["search"],
}

search_responses = {
    "response_model": SearchResponse,
    "summary": "Execute a custom search",
    "description": "Search OpenSearch using a custom DSL query.",
    "responses": {
        400: {"description": "Invalid search query."},
        500: {"description": "Internal server error."},
    },
    "tags": ["search"],
}

generate_query_responses = {
    "response_model": GenerateQueryResponse,
    "summary": "Generate a search query",
    "description": "Generate and execute a query from a user prompt.",
    "responses": {
        400: {"description": "Invalid prompt."},
        500: {"description": "Internal server error."},
    },
    "tags": ["search"],
}

user_query_responses = {
    "response_model": UserQueryResponse,
    "summary": "Build the query DSL",
    "description": "Build a hybrid query DSL for a user query.",
    "responses": {
        400: {"description": "Invalid query."},
        500: {"description": "Internal server error."},
    },
    "tags": ["search"],
}

answer_responses = {
    "response_model": AnswerResponse,
    "summary": "Generate an answer",
    "description": "Generate an answer using the RAG pipeline.",
    "responses": {
        400: {"description": "Invalid query."},
        500: {"description": "Internal server error."},
    },
    "tags": ["search"],
}
