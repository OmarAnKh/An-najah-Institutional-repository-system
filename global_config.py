from pydantic import BaseSettings


class GlobalConfig(BaseSettings):
    opensearch_host: str = "localhost"
    opensearch_port: int = 9200
    index_name: str = "documents"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
