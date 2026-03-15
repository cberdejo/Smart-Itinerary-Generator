from pydantic import Field
from pydantic_settings import BaseSettings


class ServiceSettings(BaseSettings):
    embedding_model: str = Field(
        "sentence-transformers/all-MiniLM-L6-v2", alias="EMBEDDING_MODEL"
    )
    reranker_model: str = Field(
        "cross-encoder/ms-marco-MiniLM-L-6-v2", alias="RERANKER_MODEL"
    )

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = ServiceSettings()
