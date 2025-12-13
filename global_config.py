from pydantic_settings import BaseSettings, SettingsConfigDict


class GlobalConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    opensearch_host: str 
    opensearch_port: int
    opensearch_username: str
    opensearch_password: str
    index_name: str = "documents"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"


global_config = GlobalConfig()
