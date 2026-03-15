import httpx

from config.settings import settings


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).split())


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
        asset_text = _clean_text(str(asset))
        if asset_text:
            parts.append(asset_text)

    for asset in (getattr(municipality, "intangible_assets", None) or []):
        asset_text = _clean_text(str(asset))
        if asset_text:
            parts.append(asset_text)

    return " ".join(parts).strip()


def _municipality_to_payload(municipality) -> dict:
    real_estate_assets = getattr(municipality, "real_estate_assets", None) or []
    intangible_assets = getattr(municipality, "intangible_assets", None) or []
    return {
        "name": getattr(municipality, "name", None),
        "province_name": getattr(municipality, "province_name", None),
        "capital": getattr(municipality, "capital", None),
        "has_beach": getattr(municipality, "has_beach", None),
        "description": getattr(municipality, "description", None),
        "history": getattr(municipality, "history", None),
        "real_estate_assets": [str(asset) for asset in real_estate_assets],
        "intangible_assets": [str(asset) for asset in intangible_assets],
    }


def build_search_texts_from_municipalities(municipalities: list) -> list[str]:
    if not municipalities:
        return []

    try:
        base_url = str(settings.semantic_embeddings_url).rstrip("/")
        payload = {
            "municipalities": [
                _municipality_to_payload(municipality) for municipality in municipalities
            ]
        }
        with httpx.Client(timeout=settings.semantic_embeddings_timeout_seconds) as client:
            response = client.post(f"{base_url}/search-text/municipalities", json=payload)
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
