from sentence_transformers import SentenceTransformer
from opensearchpy import OpenSearch


class ProjectMapping:
    def __init__(self, model_name: str, opensearch_host: str, opensearch_port: int):
        self.model = SentenceTransformer(model_name)
        self.model_dimension = self.model.get_sentence_embedding_dimension()
        self.client = OpenSearch(
            hosts=[{"host": opensearch_host, "port": opensearch_port}],
            use_ssl=False,
            verify_certs=False,
        )

    def encode_text(self, text: str):
        return self.model.encode([text])[0]

    def create_configurations(self):
        configurations = {
            "settings": {
                "analysis": {
                    "tokenizer": {
                        "autocomplete_tokenizer": {
                            "type": "edge_ngram",
                            "min_gram": 3,
                            "max_gram": 15,
                            "token_chars": ["letter", "digit"],
                        }
                    },
                    "filter": {
                        "english_stop": {
                            "type": "stop",
                            "stopwords": "_english_",
                        },
                        "arabic_stop": {
                            "type": "stop",
                            "stopwords": "_arabic_",
                        },
                    },
                    "analyzer": {
                        "autocomplete": {
                            "type": "custom",
                            "tokenizer": "autocomplete_tokenizer",
                            "filter": ["lowercase"],
                        },
                        "autocomplete_search": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase"],
                        },
                        "my_default_text_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "english_stop", "arabic_stop"],
                        },
                    },
                },
            },
            "mappings": {
                "properties": {
                    "collection": {"type": "keyword"},
                    "uuid": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "analyzer": "autocomplete",
                        "search_analyzer": "autocomplete_search",
                    },
                    "author": {"type": "keyword"},
                    "abstract": {
                        "type": "text",
                        "analyzer": "my_default_text_analyzer",
                    },
                    "abstract_vector": {
                        "type": "knn_vector",  # can be changed to ANN
                        "dimension": self.model_dimension,
                        "space_type": "l2",  # can be changed
                        "method": {
                            "name": "hnsw",
                            "space_type": "l2",
                            "engine": "faiss",
                            "parameters": {"ef_construction": 100, "m": 16},
                        },
                    },
                    "hasFiles": {"type": "boolean"},
                    "publicationDate": {"type": "date"},
                    "reportLocation": {"type": "geo_point"},
                    "ContentGeoPoint": {"type": "geo_point"},
                    "contentTemporalExpression": {
                        "type": "text",
                        "analyzer": "my_default_text_analyzer",
                    },
                }
            },
        }
        return configurations

    def index_document(self, index_name: str, doc_id: str, text: str):
        vector = self.encode_text(text)
        document = {"text": text, "vector": vector.tolist()}
        self.client.index(index=index_name, id=doc_id, body=document)
