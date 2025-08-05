from pydantic import BaseModel


class ImageTownOut(BaseModel):
    url: str
    model_config = {"from_attributes": True}


class RealEstateOut(BaseModel):
    name: str
    description: str | None = None
    typologies: list[dict[str, object]] = None
    characterization: str | None = None

    model_config = {"from_attributes": True}


class IntangibleOut(BaseModel):
    name: str
    scope: str | None = None
    typology: str | None = None
    description: str | None = None
    date: str | None = None

    model_config = {"from_attributes": True}


class TownOut(BaseModel):
    municipality_ine: str
    municipality_name: str
    description: str | None = None
    history: str | None = None
    capital_city: bool
    latitude: float
    longitude: float
    province_identifier: str
    province_name: str
    has_beach: bool
    images: list[ImageTownOut] = []
    real_estate_assets: list[RealEstateOut] = []
    intangible_assets: list[IntangibleOut] = []

    model_config = {"from_attributes": True}
