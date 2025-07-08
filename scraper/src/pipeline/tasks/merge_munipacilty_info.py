from prefect import task
from collections import defaultdict
from typing import Optional, List
from models.municipality import (
    MunicipalityInfo,
    BaseModel,
)


def normalize_municipality_name(name: str) -> str:
    """
    Normalize a municipality name by converting it to lowercase, stripping whitespace,
    and reformatting names that start with Spanish articles ("el", "la", "los", "las").
    If the name starts with one of these articles, the article is moved to the end
    and enclosed in parentheses. For example, "El Pueblo" becomes "pueblo (el)".
    Args:
        name (str): The original municipality name.
    Returns:
        str: The normalized municipality name.
    """

    name = name.lower().strip()
    if name.startswith(("el ", "la ", "los ", "las ")):
        parts = name.split(" ", 1)
        article = parts[0]
        main_name = parts[1]
        name = f"{main_name} ({article})"
    return name


def _safe_get_ine(ine_value: Optional[str | int]) -> Optional[str]:
    return str(ine_value) if ine_value is not None else None


def group_assets_by_municipality(
    assets: List[BaseModel], key: str = "municipality_name"
) -> dict[str, list[BaseModel]]:
    grouped = defaultdict(list)
    for asset in assets:
        name = getattr(asset, key, None)
        if name:
            normalized = normalize_municipality_name(name)
            grouped[normalized].append(asset)
    return grouped


@task
def build_municipality_info_list(
    towns_data: list[dict], beach_towns: list[str], iaph_data: dict
) -> list[MunicipalityInfo]:
    municipality_info_list = []

    beach_towns_normalized = {normalize_municipality_name(town) for town in beach_towns}

    real_estate_assets_grouped = group_assets_by_municipality(
        iaph_data.get("real_estate_assets", [])
    )
    intangible_assets_grouped = group_assets_by_municipality(
        iaph_data.get("intangible", [])
    )

    for town in towns_data:
        name = town.get("municipality_name")
        if not name:
            continue

        town_name_normalized = normalize_municipality_name(name)
        ine = _safe_get_ine(town.get("municipality_ine"))

        municipality = MunicipalityInfo(
            name=name,
            ine=ine,
            capital=town.get("capital_city"),
            latitude=town.get("latitude"),
            longitude=town.get("longitude"),
            description=town.get("description"),
            history=town.get("history"),
            images=town.get("images"),
            has_beach=town_name_normalized in beach_towns_normalized,
            real_estate_assets=real_estate_assets_grouped.get(town_name_normalized, []),
            intangible_assets=intangible_assets_grouped.get(town_name_normalized, []),
            province_identifier=town.get("province_identifier"),
            province_name=town.get("province_name", ""),
        )
        municipality_info_list.append(municipality)

    return municipality_info_list
