import pytest

from pipeline.tasks.merge_municipality_info import (
    normalize_municipality_name,
    group_assets_by_municipality,
    build_municipality_info_list,
)
from models.municipality import (
    BaseModel,
    IntangibleAsset,
    RealEstateAsset,
    RealEstateTypology,
)


class Dummy(BaseModel):
    municipality_name: str
    value: int


def test_normalize_municipality_name_articles():
    assert normalize_municipality_name("El Puerto") == "puerto (el)"
    assert normalize_municipality_name("La Línea") == "línea (la)"
    assert normalize_municipality_name("Los Barrios") == "barrios (los)"
    assert normalize_municipality_name("Las Cabezas") == "cabezas (las)"


def test_normalize_municipality_name_trim_and_case():
    assert normalize_municipality_name("  Málaga  ") == "málaga"
    assert normalize_municipality_name("Sevilla") == "sevilla"


def test_group_assets_by_municipality_keeps_normalized_keys():
    assets = [
        Dummy(municipality_name="El Puerto", value=1),
        Dummy(municipality_name="el puerto", value=2),
        Dummy(municipality_name="Málaga", value=3),
    ]
    grouped = group_assets_by_municipality(assets)
    assert set(grouped.keys()) == {"puerto (el)", "málaga"}
    assert [a.value for a in grouped["puerto (el)"]] == [1, 2]


def test_build_municipality_info_list_happy_path(
    sample_municipality_info_data_as_dict, iaph_assets
):
    """Test successful merging of town data with assets"""
    result = build_municipality_info_list.fn(
        towns_data=[sample_municipality_info_data_as_dict],
        beach_towns=["El Puerto"],
        iaph_data=iaph_assets,
    )

    assert len(result) == 1
    town = result[0]

    # Verify basic town data
    assert town.name == "El Puerto"
    assert town.ine == "11027"
    assert town.has_beach is True
    assert town.province_identifier == 11
    assert town.province_name == "Cádiz"

    # Verify assets
    assert len(town.real_estate_assets) == 1
    assert town.real_estate_assets[0].name == "Castle"
    assert town.real_estate_assets[0].typologies[0].den_tipologia == "fortress"

    assert len(town.intangible_assets) == 1
    assert town.intangible_assets[0].name == "Event"
    assert town.intangible_assets[0].typology == {"Cultural"}


def test_build_municipality_info_list_skips_missing_name():
    towns_data = [
        {"municipality_ine": 1},  # missing municipality_name
        {"municipality_name": "Sevilla", "municipality_ine": 2},
    ]
    iaph_data = {"real_estate_assets": [], "intangible": []}
    beach_towns = []
    result = build_municipality_info_list.fn(towns_data, beach_towns, iaph_data)
    assert len(result) == 1
    assert result[0].name == "Sevilla"
