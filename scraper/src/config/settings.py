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

    model_config = ConfigDict(env_file=".env")


settings = ScraperSettings()
