from src.services.open_seach_insertion import OpenSearchInsertion
from src.opensearch.open_search_client import OpenSearchClient
from src.opensearch.mapping import ProjectMapping
from src.extracters.stanza_temporal_extractor import MultiLangTemporalExtractor
from src.extracters.stanza_locations_extractor import StanzaLocationsExtractor
from src.extracters.geopy_geo_location_finder import GeopyGeoLocationFinder
from global_config import global_config

# Initialize your OpenSearch client here (not shown)
client = OpenSearchClient(True, True)
print("OpenSearch client initialized.")
project_mapping = ProjectMapping(
    model_name=global_config.embedding_model_name,
    opensearch_client=client,
)
print("Project mapping created.")
opensearch = OpenSearchInsertion(
    project_mapping,
    location_extractor=StanzaLocationsExtractor(),
    temporal_extractor=MultiLangTemporalExtractor(),
    geo_location_finder=GeopyGeoLocationFinder(),
    index_name="an_najah_repository",
)
print("OpenSearch Insertion service initialized.")
opensearch.extract_and_insert(
    jsonl_path="src/data/bulk_opensearch.jsonl",
)


print("Data insertion completed.")

# role_body = {
#     "cluster_permissions": ["cluster_composite_ops_ro"],
#     "index_permissions": [
#         {"index_patterns": ["*"], "allowed_actions": ["read", "search"]}
#     ],
# }

# response = client.transport.perform_request(
#     method="PUT", url="/_plugins/_security/api/roles/ir_readonly", body=role_body
# )

# print(response)

# role_mapping_body = {"users": ["read_only_user"]}

# response = client.transport.perform_request(
#     method="PUT",
#     url="/_plugins/_security/api/rolesmapping/ir_readonly",
#     body=role_mapping_body,
# )

# print(response)
# article_service = ArticleSearchService(index="articles", client=client_service)

# Example usage: Index an article
# article_service.index_article(
#     id="1",
#     body={"title": "Sample Article", "content": "This is a sample article."},
# )

# Example usage: Search for articles
# results = article_service.search_articles(query={"query": {"match_all": {}}})
# print(results)
