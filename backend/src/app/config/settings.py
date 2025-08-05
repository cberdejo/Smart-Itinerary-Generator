from pydantic_settings import BaseSettings
from pydantic import Field


class BackendSettings(BaseSettings):
    pguri: str = Field(..., description="Postgres URI", alias="PGURI")
    host: str = Field(..., description="Host address", alias="HOST")
    port: int = Field(..., description="Port number", alias="PORT")
    valhalla_url: str = Field(
        ..., description="Valhalla service URL", alias="VALHALLA_URL"
    )

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = BackendSettings()
