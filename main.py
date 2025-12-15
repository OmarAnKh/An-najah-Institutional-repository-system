from src.services.article_search_service import ArticleSearchService
from src.opensearch.open_search_client import OpenSearchClient


# Initialize your OpenSearch client here (not shown)
client = OpenSearchClient(True, True)

article_service = ArticleSearchService(index="articles", client=client)

# # Example usage: Index an article
# article_service.index_article(
#     id="1",
#     body={"title": "Sample Article", "content": "This is a sample article."},
# )

# Example usage: Search for articles
# results = article_service.search_articles(
#  query={"query": {"match_all": {}}}
# )
# print(results)


result = article_service.client_health()
print(result)
