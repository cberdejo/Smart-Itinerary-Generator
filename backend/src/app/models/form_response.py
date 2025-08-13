from typing import Literal
from pydantic import BaseModel, field_validator


class Coordinate(BaseModel):
    lat: float
    lng: float


class Location(Coordinate):
    label: str | None


class FormResponse(BaseModel):
    beach: Literal["yes", "no", "indiference"]
    location: Location | None
    travelTimeLimit: int | None
    culturalInfluences: str | None
    environment: str | None
    historicalPeriods: str | None
    monuments: str | None
    traditions: str | None
    travelInterests: str | None
    villageType: str | None

    @field_validator("*", mode="before")
    @classmethod
    def empty_string_to_none(cls, v, info):
        """
        Convert empty strings to None

        Args:
            v (_type_): _description_
            info (_type_): _description_

        Returns:
            _type_: _description_
        """
        if info.field_name == "beach" and v == "":
            return "indiference"
        return v if v != "" else None

    @field_validator("travelTimeLimit", mode="before")
    @classmethod
    def convert_travel_time_limit(cls, v):
        """
        Convert travelTimeLimit to int

        Args:
            v (_type_): _description_

        Raises:
            ValueError: travelTimeLimit must be an integer

        Returns:
            _type_: _description_
        """
        if v is None or v == "" or isinstance(v, int):
            return v
        try:
            return int(v)
        except (ValueError, TypeError):
            raise ValueError("travelTimeLimit must be an integer")

    def get_embedding_text(self) -> str:
        """
        Get the embedding text

        Returns:
            str: _description_
        """
        parts = []

        if self.villageType:
            parts.append(self.villageType.strip())

        if self.environment:
            parts.append(self.environment.strip())

        if self.monuments:
            parts.append(f"Interesado en monumentos como: {self.monuments.strip()}")

        if self.historicalPeriods:
            parts.append(
                f"Épocas históricas de interés: {self.historicalPeriods.strip()}"
            )

        if self.culturalInfluences:
            parts.append(
                f"Culturas que me interesan: {self.culturalInfluences.strip()}"
            )

        if self.travelInterests:
            parts.append(self.travelInterests.strip())

        if self.traditions:
            parts.append(
                f"Tradiciones o festividades que me gustaría experimentar: {self.traditions.strip()}"
            )

        return " ".join(parts)
