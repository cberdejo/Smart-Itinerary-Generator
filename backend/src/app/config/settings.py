from pydantic_settings import BaseSettings
from pydantic import Field


class BackendSettings(BaseSettings):
    host: str = Field("0.0.0.0", description="Host address", alias="HOST")
    port: int = Field(8000, description="Port number", alias="PORT")
    pguri: str = Field(..., description="Postgres URI", alias="PGURI")
    valhalla_url: str = Field(
        ..., description="Valhalla service URL", alias="VALHALLA_URL"
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
    reranker_model: str = Field(
        "cross-encoder/ms-marco-MiniLM-L-6-v2",
        description="Reranker model to use in semantic-embeddings API",
        alias="RERANKER_MODEL",
    )
    semantic_embeddings_timeout_seconds: float = Field(
        30.0,
        description="HTTP timeout for semantic-embeddings API calls",
        alias="SEMANTIC_EMBEDDINGS_TIMEOUT_SECONDS",
    )

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = BackendSettings()
