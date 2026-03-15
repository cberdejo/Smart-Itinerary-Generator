from service.schemas import SearchTextTown


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).split())


def build_search_text_from_town(town: SearchTextTown) -> str:
    parts: list[str] = []

    name = _clean_text(town.municipality_name)
    if name:
        parts.append(f"Municipio: {name}.")

    province_name = _clean_text(town.province_name)
    if province_name:
        parts.append(f"Provincia: {province_name}.")

    if town.capital_city is not None:
        parts.append(
            "Es capital de provincia."
            if town.capital_city
            else "No es capital de provincia."
        )

    if town.has_beach is not None:
        parts.append("Tiene playa." if town.has_beach else "No tiene playa.")

    description = _clean_text(town.description)
    if description:
        parts.append(f"Descripcion: {description}")

    history = _clean_text(town.history)
    if history:
        parts.append(f"Historia: {history}")

    for asset in town.real_estate_assets:
        asset_name = _clean_text(asset.name)
        desc = _clean_text(asset.description)
        characterization = _clean_text(asset.characterization)
        typologies = asset.typologies or []
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

    for asset in town.intangible_assets:
        asset_name = _clean_text(asset.name)
        scope = _clean_text(asset.scope)
        typology = _clean_text(asset.typology)
        asset_description = _clean_text(asset.description)
        date = _clean_text(asset.date)
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

    return " ".join([part for part in parts if part]).strip()
