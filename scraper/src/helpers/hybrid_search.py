import httpx

from config.settings import settings


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).split())


def _serialize_typologies(typologies) -> list:
    return [
        typology.model_dump() if hasattr(typology, "model_dump") else typology
        for typology in (typologies or [])
    ]


def _serialize_typology(typology) -> str | None:
    if typology is None:
        return None
    if isinstance(typology, str):
        return typology
    if isinstance(typology, set):
        return ", ".join(sorted(str(value) for value in typology if value))
    if isinstance(typology, (list, tuple)):
        return ", ".join(str(value) for value in typology if value)
    return str(typology)


def _fallback_build_search_text_from_municipality(municipality) -> str:
    parts: list[str] = []

    name = _clean_text(getattr(municipality, "name", None))
    if name:
        parts.append(f"Municipio: {name}.")

    province_name = _clean_text(getattr(municipality, "province_name", None))
    if province_name:
        parts.append(f"Provincia: {province_name}.")

    capital = getattr(municipality, "capital", None)
    if capital is not None:
        parts.append(
            "Es capital de provincia." if capital else "No es capital de provincia."
        )

    has_beach = getattr(municipality, "has_beach", None)
    if has_beach is not None:
        parts.append("Tiene playa." if has_beach else "No tiene playa.")

    description = _clean_text(getattr(municipality, "description", None))
    if description:
        parts.append(f"Descripcion: {description}")

    history = _clean_text(getattr(municipality, "history", None))
    if history:
        parts.append(f"Historia: {history}")

    for asset in (getattr(municipality, "real_estate_assets", None) or []):
        asset_name = _clean_text(getattr(asset, "name", None))
        desc = _clean_text(getattr(asset, "description", None))
        characterization = _clean_text(getattr(asset, "characterization", None))
        typologies = _clean_text(
            _serialize_typologies(getattr(asset, "typologies", None))
        )
        parts.append(
            " ".join(
                [
                    f"Patrimonio inmueble: {asset_name}." if asset_name else "",
                    f"Descripcion: {desc}." if desc else "",
                    f"Caracterizacion: {characterization}."
                    if characterization
                    else "",
                    f"Tipologias: {typologies}." if typologies else "",
                ]
            ).strip()
        )

    for asset in (getattr(municipality, "intangible_assets", None) or []):
        asset_name = _clean_text(getattr(asset, "name", None))
        scope = _clean_text(getattr(asset, "scope", None))
        typology = _clean_text(
            _serialize_typology(getattr(asset, "typology", None))
        )
        asset_description = _clean_text(getattr(asset, "description", None))
        date = _clean_text(getattr(asset, "date", None))
        parts.append(
            " ".join(
                [
                    f"Patrimonio inmaterial: {asset_name}." if asset_name else "",
                    f"Alcance: {scope}." if scope else "",
                    f"Tipologia: {typology}." if typology else "",
                    f"Descripcion: {asset_description}."
                    if asset_description
                    else "",
                    f"Fecha: {date}." if date else "",
                ]
            ).strip()
        )

    return " ".join([part for part in parts if part]).strip()


def _municipality_to_town_payload(municipality) -> dict:
    real_estate_assets = getattr(municipality, "real_estate_assets", None) or []
    intangible_assets = getattr(municipality, "intangible_assets", None) or []
    return {
        "municipality_name": getattr(municipality, "name", None),
        "province_name": getattr(municipality, "province_name", None),
        "capital_city": getattr(municipality, "capital", None),
        "has_beach": getattr(municipality, "has_beach", None),
        "description": getattr(municipality, "description", None),
        "history": getattr(municipality, "history", None),
        "real_estate_assets": [
            {
                "name": getattr(asset, "name", None),
                "description": getattr(asset, "description", None),
                "characterization": getattr(asset, "characterization", None),
                "typologies": _serialize_typologies(
                    getattr(asset, "typologies", None)
                ),
            }
            for asset in real_estate_assets
        ],
        "intangible_assets": [
            {
                "name": getattr(asset, "name", None),
                "scope": getattr(asset, "scope", None),
                "typology": _serialize_typology(getattr(asset, "typology", None)),
                "description": getattr(asset, "description", None),
                "date": getattr(asset, "date", None),
            }
            for asset in intangible_assets
        ],
    }


def build_search_texts_from_municipalities(municipalities: list) -> list[str]:
    if not municipalities:
        return []

    try:
        base_url = str(settings.semantic_embeddings_url).rstrip("/")
        payload = {
            "towns": [
                _municipality_to_town_payload(municipality)
                for municipality in municipalities
            ]
        }
        with httpx.Client(timeout=settings.semantic_embeddings_timeout_seconds) as client:
            response = client.post(f"{base_url}api/v1/search-text/towns", json=payload)
            response.raise_for_status()
            data = response.json()

        texts = data.get("texts")
        if not isinstance(texts, list):
            raise RuntimeError("Invalid search-text response format")

        return [str(text) for text in texts]
    except Exception:
        return [
            _fallback_build_search_text_from_municipality(municipality)
            for municipality in municipalities
        ]


def build_search_text_from_municipality(municipality) -> str:
    texts = build_search_texts_from_municipalities([municipality])
    return texts[0] if texts else ""
