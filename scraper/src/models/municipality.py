from pydantic import BaseModel


class RealEstateAsset(BaseModel):
    name: str
    municipality_name: str
    description: str | None
    typologies: list[dict]
    characterization: str | None

    def __str__(self):
        desc = self.description or "sin descripción"
        types = (
            ", ".join([t.get("type", "tipo desconocido") for t in self.typologies])
            if self.typologies
            else "sin tipologías"
        )
        char = self.characterization or "sin caracterización"
        return f"El bien inmueble '{self.name}' se caracteriza por: {desc}. Tipologías: {types}. Caracterización: {char}."


class IntangibleAsset(BaseModel):
    name: str
    municipality_name: str
    scope: str | None
    typology: str | None
    description: str | None
    date: str | None

    def __str__(self):
        desc = self.description or "sin descripción"
        tip = self.typology or "tipología no especificada"
        scope = self.scope or "ámbito no definido"
        date = self.date or "fecha no especificada"
        return f"El bien inmaterial '{self.name}'. Es un inmaterial de tipo {tip}, con un alcance {scope}. Descripción: {desc}. Fecha: {date}."


class MunicipalityInfo(BaseModel):
    name: str
    description: str | None
    history: str | None
    images: list[str] | None
    ine: str | None
    capital: bool | None
    latitude: float | None
    longitude: float | None
    has_beach: bool
    real_estate_assets: list[RealEstateAsset]
    intangible_assets: list[IntangibleAsset]
    province_identifier: int | None
    province_name: str | None

    def get_embedding_text(self) -> str:
        parts = []
        parts = [f"{self.name or 'Municipio desconocido'} es un municipio"]

        parts.append(
            "que es capital de provincia."
            if self.capital
            else "que no es capital de provincia."
        )

        if self.description:
            parts.append(f"{self.description}")

        if self.history:
            parts.append(f"{self.history}")

        for asset in self.real_estate_assets:
            parts.append(str(asset))

        for intangible in self.intangible_assets:
            parts.append(str(intangible))

        return " ".join(parts)
