from src.services.open_seach_insertion import OpenSearchInsertion
from src.opensearch.open_search_client import OpenSearchClient
from src.opensearch.mapping import ProjectMapping
from src.extracters.stanza_temporal_extractor import MultiLangTemporalExtractor
from src.extracters.stanza_locations_extractor import StanzaLocationsExtractor
from src.extracters.geopy_geo_location_finder import GeopyGeoLocationFinder
from src.services.an_najah_repository_search_service import (
    AnNajahRepositorySearchService,
)
from global_config import global_config
from fastapi import FastAPI, Query

# Initialize FastAPI app
main = FastAPI()

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
)

# autocomplete API endpoint
@main.get("/api/suggest")
def suggest(
    q: str = Query(..., min_length=3),
    limit: int = Query(8, ge=1, le=20)
):
    # return a raw list[str] of suggestions
    return opensearch_search_service.suggest(prefix=q, limit=limit)

print(opensearch_search_service.client_health())
