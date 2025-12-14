from sentence_transformers import SentenceTransformer
from opensearchpy import OpenSearch


class ProjectMapping:
    """Configure OpenSearch mappings and encode text with a sentence-transformer.

    This class owns the sentence-transformer model, the OpenSearch client,
    and the index settings/mappings used for the institutional repository.
    """

    def __init__(self, model_name: str, opensearch_host: str, opensearch_port: int):
        """Initialize the model and OpenSearch client.

        Args:
            model_name: Name of the sentence-transformer model to load.
            opensearch_host: Hostname or IP address of the OpenSearch node.
            opensearch_port: Port on which OpenSearch is listening.
        """

        self.model = SentenceTransformer(model_name)
        self.model_dimension = self.model.get_sentence_embedding_dimension()
        self.tokenizer = self.model.tokenizer
        self.client = OpenSearch(
            hosts=[{"host": opensearch_host, "port": opensearch_port}],
            use_ssl=False,
            verify_certs=False,
        )

    def encode_text(self, text: str):
        """Encode a piece of text into a dense vector using the model."""

        return self.model.encode([text])[0]
    
    def chunk_text(self, text: str, max_tokens: int = 450, overlap: int = 50):
        """Chunk the input text into smaller pieces based on token count.

        Args:
            text (str): _input text to be chunked.
            max_tokens (int, optional): Maximum number of tokens per chunk. Defaults to 450.
            overlap (int, optional): Number of tokens to overlap between chunks. Defaults to 50.

        Returns:
            List[str]: List of text chunks.
        """

        if not text:
            return []
        
        chunks = []
        token_ids = self.tokenizer.encode(text, add_special_tokens=False)
        start = 0
        step = max_tokens - overlap
        while start < len(token_ids):
            end = min(start + max_tokens, len(token_ids))
            chunk_tokens = token_ids[start:end]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
            start += step
            
        return chunks
    
    def create_index(self, index_name: str):
        """Create the OpenSearch index with the configured mappings/settings if needed."""

        configurations = self.create_configurations()
        if not self.client.indices.exists(index=index_name):
            self.client.indices.create(index=index_name, body=configurations)

    def create_configurations(self):
        """Return the OpenSearch index settings and mappings dictionary."""

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
                        "type": "object",
                        "properties": {
                            "en": {
                                "type": "knn_vector",
                                "dimension": self.model_dimension,
                                "space_type": "cosinesimil",
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
                            "ar": {
                                "type": "knn_vector",
                                "dimension": self.model_dimension,
                                "space_type": "cosinesimil",
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
                        },
                        "dynamic": False,
                    },
                    "hasFiles": {
                        "type": "boolean",
                        "boost": 3.0,  # gives more importance to documents with files
                    },
                    "publicationDate": {"type": "date"},
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
        """Index a single text document into the given index.

        A vector representation of the text is computed and stored alongside
        the raw text under the ``vector`` field.
        """

        vector = self.encode_text(text)
        document = {"text": text, "vector": vector.tolist()}
        self.client.index(index=index_name, id=doc_id, body=document)
