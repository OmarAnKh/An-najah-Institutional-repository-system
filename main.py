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
from src.queries_generation.query_generation import QueryGeneration

query_generation = QueryGeneration(ollama_model=global_config.generative_model_name)
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
)

generated_query = opensearch_search_service.generate_query(
    user_prompt="Find articles related to climate change published after 2020."
)


print("Generated Query:", generated_query[1])

# print(opensearch_search_service.client_health())
