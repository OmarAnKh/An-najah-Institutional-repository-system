import os

import boto3
from pydantic_settings import BaseSettings, SettingsConfigDict


class GlobalConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    opensearch_host: str
    opensearch_port: int
    index_name: str = "documents"
    embedding_model_name: str
    aws_region: str
    aws_secret_access_key: str
    aws_access_key_id: str
    pipeline_name: str
    suggest_url: str
    generative_model_name: str
    google_api_key: str
    ollama_model_name: str

global_config = GlobalConfig()

os.environ["AWS_ACCESS_KEY_ID"] = global_config.aws_access_key_id
os.environ["AWS_SECRET_ACCESS_KEY"] = global_config.aws_secret_access_key
os.environ["AWS_REGION"] = global_config.aws_region
os.environ["GOOGLE_API_KEY"] = global_config.google_api_key

os.environ.pop("AWS_PROFILE", None)

boto3.setup_default_session(
    aws_access_key_id=global_config.aws_access_key_id,
    aws_secret_access_key=global_config.aws_secret_access_key,
    region_name=global_config.aws_region,
)
