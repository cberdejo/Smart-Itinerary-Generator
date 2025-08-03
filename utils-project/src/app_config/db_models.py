from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import ARRAY, Double, JSON
from pydantic import BaseModel


class Town(SQLModel, table=True):
    __tablename__ = "towns"

    municipality_ine: str = Field(primary_key=True)
    municipality_name: str | None = None
    description: str | None = None
    history: str | None = None
    capital_city: bool | None = None
    latitude: float | None = Field(default=None, sa_type=Double(53))
    longitude: float | None = Field(default=None, sa_type=Double(53))
    province_identifier: str | None = None
    province_name: str | None = None
    has_beach: bool | None = None
    embeddings: list | None = Field(default=None, sa_type=ARRAY(Double(precision=53)))

    images: list["Image"] = Relationship(back_populates="towns")
    intangible_assets: list["Intangible"] = Relationship(back_populates="towns")
    real_estate_assets: list["RealEstate"] = Relationship(back_populates="towns")


class Image(SQLModel, table=True):
    __tablename__ = "images"

    url: str = Field(primary_key=True)
    municipality_ine: str = Field(
        primary_key=True, foreign_key="towns.municipality_ine"
    )

    towns: "Town" = Relationship(back_populates="images")


class Intangible(SQLModel, table=True):
    __tablename__ = "intangible_assets"

    municipality_ine: str = Field(
        primary_key=True, foreign_key="towns.municipality_ine"
    )
    name: str = Field(primary_key=True)
    scope: str | None = None
    typology: str | None = None
    description: str | None = None
    date: str | None = None

    towns: "Town" = Relationship(back_populates="intangible_assets")


class RealEstate(SQLModel, table=True):
    __tablename__ = "real_estate_assets"

    municipality_ine: str = Field(
        primary_key=True, foreign_key="towns.municipality_ine"
    )
    name: str = Field(primary_key=True)
    description: str | None = None
    typologies: list[dict] | None = Field(default=None, sa_type=JSON)
    characterization: str | None = None
    towns: "Town" = Relationship(back_populates="real_estate_assets")
