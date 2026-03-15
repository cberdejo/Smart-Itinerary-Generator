from pydantic import BaseModel, Field


class EmbedRequest(BaseModel):
    input: str | list[str]
    model: str | None = None


class EmbedResponse(BaseModel):
    embeddings: list[list[float]]


class RerankRequest(BaseModel):
    query: str
    documents: list[str]
    model: str | None = None


class RerankResponse(BaseModel):
    scores: list[float]


class SearchTextTownAsset(BaseModel):
    name: str | None = None
    description: str | None = None
    characterization: str | None = None
    typologies: list[dict] | None = None


class SearchTextIntangibleAsset(BaseModel):
    name: str | None = None
    scope: str | None = None
    typology: str | None = None
    description: str | None = None
    date: str | None = None


class SearchTextTown(BaseModel):
    municipality_name: str | None = None
    province_name: str | None = None
    capital_city: bool | None = None
    has_beach: bool | None = None
    description: str | None = None
    history: str | None = None
    real_estate_assets: list[SearchTextTownAsset] = Field(default_factory=list)
    intangible_assets: list[SearchTextIntangibleAsset] = Field(default_factory=list)


class SearchTextMunicipality(BaseModel):
    name: str | None = None
    province_name: str | None = None
    capital: bool | None = None
    has_beach: bool | None = None
    description: str | None = None
    history: str | None = None
    real_estate_assets: list[object] = Field(default_factory=list)
    intangible_assets: list[object] = Field(default_factory=list)


class SearchTownTextRequest(BaseModel):
    town: SearchTextTown


class SearchTownTextsRequest(BaseModel):
    towns: list[SearchTextTown]


class SearchMunicipalityTextRequest(BaseModel):
    municipality: SearchTextMunicipality


class SearchMunicipalityTextsRequest(BaseModel):
    municipalities: list[SearchTextMunicipality]


class SearchTextResponse(BaseModel):
    text: str


class SearchTextsResponse(BaseModel):
    texts: list[str]
