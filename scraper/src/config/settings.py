from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict


class ScraperSettings(BaseSettings):
    pguri: str = Field(..., description="Postgres URI", alias="PGURI")
    minio_user: str = Field(..., description="Minio root user", alias="MINIO_ROOT_USER")
    minio_password: str = Field(
        ..., description="Minio root password", alias="MINIO_ROOT_PASSWORD"
    )
    minio_url: str = Field(
        ...,
        description="Minio endpoint with this format host:port",
        alias="MINIO_ENDPOINT",
    )
    semantic_embeddings_url: str = Field(
        "http://semantic-embeddings:8080",
        description="Semantic embeddings API base URL",
        alias="SEMANTIC_EMBEDDINGS_URL",
    )
    embedding_model: str = Field(
        "sentence-transformers/all-MiniLM-L6-v2",
        description="Embedding model to use in semantic-embeddings API",
        alias="EMBEDDING_MODEL",
    )
    semantic_embeddings_timeout_seconds: float = Field(
        30.0,
        description="HTTP timeout for semantic-embeddings API calls",
        alias="SEMANTIC_EMBEDDINGS_TIMEOUT_SECONDS",
    )

    model_config = ConfigDict(env_file=".env")


settings = ScraperSettings()
