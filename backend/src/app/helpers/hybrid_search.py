import httpx

from app.config.settings import settings


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).split())


def _fallback_build_search_text_from_town(town) -> str:
    parts: list[str] = []

    name = _clean_text(getattr(town, "municipality_name", None))
    if name:
        parts.append(f"Municipio: {name}.")

    province_name = _clean_text(getattr(town, "province_name", None))
    if province_name:
        parts.append(f"Provincia: {province_name}.")

    capital_city = getattr(town, "capital_city", None)
    if capital_city is not None:
        parts.append(
            "Es capital de provincia."
            if capital_city
            else "No es capital de provincia."
        )

    has_beach = getattr(town, "has_beach", None)
    if has_beach is not None:
        parts.append("Tiene playa." if has_beach else "No tiene playa.")

    description = _clean_text(getattr(town, "description", None))
    if description:
        parts.append(f"Descripcion: {description}")

    history = _clean_text(getattr(town, "history", None))
    if history:
        parts.append(f"Historia: {history}")

    for asset in (getattr(town, "real_estate_assets", None) or []):
        asset_name = _clean_text(getattr(asset, "name", None))
        desc = _clean_text(getattr(asset, "description", None))
        characterization = _clean_text(getattr(asset, "characterization", None))
        typologies = getattr(asset, "typologies", None) or []
        parts.append(
            " ".join(
                [
                    f"Patrimonio inmueble: {asset_name}." if asset_name else "",
                    f"Descripcion: {desc}." if desc else "",
                    f"Caracterizacion: {characterization}." if characterization else "",
                    f"Tipologias: {typologies}." if typologies else "",
                ]
            ).strip()
        )

    for asset in (getattr(town, "intangible_assets", None) or []):
        asset_name = _clean_text(getattr(asset, "name", None))
        scope = _clean_text(getattr(asset, "scope", None))
        typology = _clean_text(getattr(asset, "typology", None))
        asset_description = _clean_text(getattr(asset, "description", None))
        date = _clean_text(getattr(asset, "date", None))
        parts.append(
            " ".join(
                [
                    f"Patrimonio inmaterial: {asset_name}." if asset_name else "",
                    f"Alcance: {scope}." if scope else "",
                    f"Tipologia: {typology}." if typology else "",
                    f"Descripcion: {asset_description}." if asset_description else "",
                    f"Fecha: {date}." if date else "",
                ]
            ).strip()
        )

    return " ".join([p for p in parts if p]).strip()


def _town_to_payload(town) -> dict:
    return {
        "municipality_name": getattr(town, "municipality_name", None),
        "province_name": getattr(town, "province_name", None),
        "capital_city": getattr(town, "capital_city", None),
        "has_beach": getattr(town, "has_beach", None),
        "description": getattr(town, "description", None),
        "history": getattr(town, "history", None),
        "real_estate_assets": [
            {
                "name": getattr(asset, "name", None),
                "description": getattr(asset, "description", None),
                "characterization": getattr(asset, "characterization", None),
                "typologies": getattr(asset, "typologies", None) or [],
            }
            for asset in (getattr(town, "real_estate_assets", None) or [])
        ],
        "intangible_assets": [
            {
                "name": getattr(asset, "name", None),
                "scope": getattr(asset, "scope", None),
                "typology": getattr(asset, "typology", None),
                "description": getattr(asset, "description", None),
                "date": getattr(asset, "date", None),
            }
            for asset in (getattr(town, "intangible_assets", None) or [])
        ],
    }


def build_search_texts_from_towns(towns: list) -> list[str]:
    if not towns:
        return []

    try:
        base_url = str(settings.semantic_embeddings_url).rstrip("/")
        payload = {"towns": [_town_to_payload(town) for town in towns]}

        with httpx.Client(timeout=settings.semantic_embeddings_timeout_seconds) as client:
            response = client.post(f"{base_url}/api/v1/search-text/towns", json=payload)
            response.raise_for_status()
            data = response.json()

        texts = data.get("texts")
        if not isinstance(texts, list):
            raise RuntimeError("Invalid search-text response format")

        return [str(text) for text in texts]
    except Exception:
        return [_fallback_build_search_text_from_town(town) for town in towns]


def build_search_text_from_town(town) -> str:
    texts = build_search_texts_from_towns([town])
    return texts[0] if texts else ""
