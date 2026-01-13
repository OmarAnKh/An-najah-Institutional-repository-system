from fastapi import FastAPI
from langchain_google_genai import ChatGoogleGenerativeAI

from global_config import global_config
from src.api.indexing.routes import router as indexing_router
from src.api.search.routes import router as search_router
from src.extracters.geopy_geo_location_finder import GeopyGeoLocationFinder
from src.extracters.stanza_locations_extractor import StanzaLocationsExtractor
from src.extracters.stanza_temporal_extractor import MultiLangTemporalExtractor
from src.models.chat_model import GeminiGenerativeModel
from src.opensearch.mapping import ProjectMapping
from src.opensearch.open_search_client import OpenSearchClient
from src.queries_generation.gemini_query_generation import GeminiQueryGeneration
from src.services.an_najah_repository_search_service import (
    AnNajahRepositorySearchService,
)
from src.services.open_seach_insertion import OpenSearchInsertion


generative_model = ChatGoogleGenerativeAI(
    model=global_config.generative_model_name,
    temperature=0.0,
)

query_generation = GeminiQueryGeneration(model=generative_model)

client = OpenSearchClient(True, True)
print("OpenSearch client initialized.")

project_mapping = ProjectMapping(
    model_name=global_config.embedding_model_name,
    opensearch_client=client,
)

opensearch_insertion_client = OpenSearchInsertion(
    project_mapping,
    location_extractor=StanzaLocationsExtractor(),
    temporal_extractor=MultiLangTemporalExtractor(),
    geo_location_finder=GeopyGeoLocationFinder(),
    index_name=global_config.index_name,
)

opensearch_search_service = AnNajahRepositorySearchService(
    index=global_config.index_name,
    client=client,
    query_generator=query_generation,
    mapping=project_mapping,
    generative_model=GeminiGenerativeModel(model=generative_model),
)

# Initialize FastAPI app
app = FastAPI()
app.state.search_service = opensearch_search_service
app.state.insertion_service = opensearch_insertion_client
app.include_router(search_router)
app.include_router(indexing_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


main = app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:main", host="0.0.0.0", port=8000)
