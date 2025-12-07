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
                "index": {"knn": True},
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
                        "english_stemmer": {
                            "type": "stemmer",
                            "language": "english",
                        },
                        "english_possessive_stemmer": {
                            "type": "stemmer",
                            "language": "possessive_english",
                        },
                        "arabic_stop": {
                            "type": "stop",
                            "stopwords": "_arabic_",
                        },
                        "arabic_stemmer": {
                            "type": "stemmer",
                            "language": "arabic",
                        },
                        "arabic_normalization": {
                            "type": "arabic_normalization",
                        },
                        "length_3_plus": {
                            "type": "length",
                            "min": 3,
                        },
                    },
                    "analyzer": {
                        "en_autocomplete": {
                            "type": "custom",
                            "tokenizer": "autocomplete_tokenizer",
                            "char_filter": ["html_strip_cf"],
                            "filter": [
                                "lowercase",
                                "english_possessive_stemmer",
                                "english_stop",
                                "english_stemmer",
                            ],
                        },
                        "en_autocomplete_search": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "char_filter": ["html_strip_cf"],
                            "filter": [
                                "lowercase",
                                "english_possessive_stemmer",
                                "english_stop",
                                "english_stemmer",
                                "length_3_plus",
                            ],
                        },
                        "en_content": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "char_filter": ["html_strip_cf"],
                            "filter": [
                                "lowercase",
                                "english_possessive_stemmer",
                                "english_stop",
                                "english_stemmer",
                            ],
                        },
                        "ar_autocomplete": {
                            "type": "custom",
                            "tokenizer": "autocomplete_tokenizer",
                            "char_filter": ["html_strip_cf"],
                            "filter": [
                                "arabic_normalization",
                                "arabic_stop",
                                "arabic_stemmer",
                            ],
                        },
                        "ar_autocomplete_search": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "char_filter": ["html_strip_cf"],
                            "filter": [
                                "arabic_normalization",
                                "arabic_stop",
                                "arabic_stemmer",
                            ],
                        },
                        "ar_content": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "char_filter": ["html_strip_cf"],
                            "filter": [
                                "arabic_normalization",
                                "arabic_stop",
                                "arabic_stemmer",
                            ],
                        },
                    },
                    "normalizer": {
                        "keyword_lowercase": {"type": "custom", "filter": ["lowercase"]}
                    },
                },
            },
            "mappings": {
                "properties": {
                    "collection": {
                        "type": "keyword",
                        "doc_values": True,  # add it to enable sorting and aggregations default is true
                    },
                    "bitstream_uuid": {
                        "type": "keyword",
                        "index": False,  # to disable indexing on it (we cant search on it but it will be stored and takes less disk space)
                    },
                    "chunk_id": {
                        "type": "keyword",
                        "index": False,  # to disable indexing on it (we cant search on it but it will be stored and takes less disk space)
                    },
                    "title": {
                        "type": "object",
                        "properties": {
                            "en": {
                                "type": "text",
                                "analyzer": "en_autocomplete",
                                "search_analyzer": "en_autocomplete_search",
                            },
                            "ar": {
                                "type": "text",
                                "analyzer": "ar_autocomplete",
                                "search_analyzer": "ar_autocomplete_search",
                            },
                        },
                        "dynamic": False,
                    },
                    "author": {
                        "type": "text",
                        "analyzer": "en_autocomplete",
                        "search_analyzer": "en_autocomplete_search",
                    },
                    "abstract": {
                        "type": "object",
                        "properties": {
                            "en": {
                                "type": "text",
                                "analyzer": "en_content",
                            },
                            "ar": {
                                "type": "text",
                                "analyzer": "ar_content",
                            },
                        },
                        "dynamic": False,
                    },
                    "abstract_vector": {
                        "type": "knn_vector",  # can be changed to ANN
                        "dimension": self.model_dimension,
                        "space_type": "cosinesimil",  # can be changed
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "faiss",
                            "parameters": {
                                "ef_construction": 150,
                                "m": 32,
                            },
                        },
                    },
                    "hasFiles": {
                        "type": "boolean",
                        "boost": 3.0,  # gives more importance to documents with files
                    },
                    "publicationDate": {"type": "date"},
                    "reportLocation": {
                        "type": "geo_point",
                        "ignore_malformed": True,
                    },
                    "geoReferences": {
                        "type": "nested",
                        "properties": {
                            "placeName": {"type": "text", "analyzer": "en_content"},
                            "coordinates": {
                                "type": "geo_point",
                                "ignore_malformed": True,
                            },
                        },
                    },
                    "temporalExpressions": {"type": "keyword"},
                },
            },
        }
        return configurations

    def index_document(self, index_name: str, doc_id: str, text: str):
        vector = self.encode_text(text)
        document = {"text": text, "vector": vector.tolist()}
        self.client.index(index=index_name, id=doc_id, body=document)
