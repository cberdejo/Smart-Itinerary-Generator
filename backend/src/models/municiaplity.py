from typing import Any, List, Optional
from pydantic import BaseModel


class ImageTownOut(BaseModel):
    url: str
    model_config = {"from_attributes": True}


class RealEstateOut(BaseModel):
    name: str
    description: Optional[str]
    typologies: Optional[List[dict[str, Any]]]
    characterization: Optional[str]

    model_config = {"from_attributes": True}


class IntangibleOut(BaseModel):
    name: str
    scope: Optional[str]
    typology: Optional[str]
    description: Optional[str]
    date: Optional[str]

    model_config = {"from_attributes": True}


class TownOut(BaseModel):
    municipality_ine: str
    municipality_name: str
    description: Optional[str]
    history: Optional[str]
    capital_city: Optional[bool]
    latitude: float
    longitude: float
    province_identifier: str
    province_name: str
    has_beach: bool
    images: List[ImageTownOut] = []
    real_estate_assets: List[RealEstateOut] = []
    intangible_assets: List[IntangibleOut] = []

    model_config = {"from_attributes": True}
