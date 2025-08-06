from pydantic_settings import BaseSettings
from pydantic import Field


class BackendSettings(BaseSettings):
    host: str = Field("0.0.0.0", description="Host address", alias="HOST")
    port: int = Field(8000, description="Port number", alias="PORT")
    pguri: str = Field(..., description="Postgres URI", alias="PGURI")
    valhalla_url: str = Field(..., description="Valhalla service URL", alias="VALHALLA_URL")

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


settings = BackendSettings()
 