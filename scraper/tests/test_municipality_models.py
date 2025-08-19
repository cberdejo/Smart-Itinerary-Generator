import re
import unicodedata
import pytest

from models.municipality import RealEstateTypology


def _normalize(text: str) -> str:
    """Remove accents, collapse whitespace, and lowercase for robust comparisons."""
    if text is None:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()


@pytest.mark.parametrize(
    "kwargs, expected_contains, expected_not_contains",
    [
        # Name only
        (
            dict(
                den_tipologia="Iglesia", periodos=None, den_etnia=None, denom_acti=None
            ),
            ["iglesia"],
            ["none"],
        ),
        # With ethnicity
        (
            dict(
                den_tipologia="Ermita",
                den_etnia="Múdejar",
                periodos=None,
                denom_acti=None,
            ),
            ["ermita", "etnia: mudejar"],
            ["none"],
        ),
        # With period
        (
            dict(
                den_tipologia="Castillo",
                periodos="S. XV",
                den_etnia=None,
                denom_acti=None,
            ),
            ["castillo", "periodo: s. xv"],
            ["none"],
        ),
        # With activity
        (
            dict(
                den_tipologia="Puente",
                denom_acti="Tránsito",
                periodos=None,
                den_etnia=None,
            ),
            ["puente", "actividad: transito"],
            ["none"],
        ),
        # All fields
        (
            dict(
                den_tipologia="Torre",
                den_etnia="Bereber",
                periodos="Medieval",
                denom_acti="Vigía",
            ),
            ["torre", "etnia: bereber", "periodo: medieval", "actividad: vigia"],
            ["none"],
        ),
    ],
)
def test_realestate_typology_str_is_robust(
    kwargs, expected_contains, expected_not_contains
):
    t = RealEstateTypology(**kwargs)
    s = _normalize(str(t))
    for token in expected_contains:
        assert token in s
    for token in expected_not_contains:
        assert token not in s
    # Avoid repeated double spaces after normalization
    assert "  " not in s


# ==============================
# RealEstateAsset.__str__
# ==============================


def test_realestate_asset_str_uses_factory_and_fallbacks(real_estate_asset_factory):
    # Default factory (description=None, characterization=None)
    asset = real_estate_asset_factory()
    s = _normalize(str(asset))
    assert "test property" in s
    assert "test" in s  # typology label from default RealEstateTypology
    assert "sin descripcion" in s
    assert "sin caracterizacion" in s
    assert "none" not in s

    # Multiple typologies (both valid RealEstateTypology instances), explicit characterization
    asset2 = real_estate_asset_factory(
        name="Mixed",
        description="Something",
        typologies=[
            RealEstateTypology(den_tipologia="Puente"),
            RealEstateTypology(den_tipologia="Otro tipo"),
        ],
        characterization="Religioso",
    )
    s2 = _normalize(str(asset2))
    assert "mixed" in s2
    assert "puente" in s2 and "otro tipo" in s2
    assert "caracterizacion: religioso" in s2
    assert "none" not in s2

    # Empty name, empty typologies and characterization -> safe fallbacks
    asset3 = real_estate_asset_factory(
        name="",
        typologies=[],
        characterization="",
        description=None,
    )
    s3 = _normalize(str(asset3))
    assert isinstance(s3, str) and s3.strip() != ""
    assert "sin tipologias" in s3
    assert "sin caracterizacion" in s3
    assert "sin descripcion" in s3
    assert "none" not in s3


# ==============================
# IntangibleAsset
# ==============================


def test_intangible_asset_typology_string_is_deterministic(intangible_asset_factory):
    ia = intangible_asset_factory(typology={"Tradicion", "Costumbre", "Rito"})
    s = ia.typology_string()
    assert s.split(", ") == sorted(s.split(", "))


@pytest.mark.parametrize(
    "typology, scope, description, date, expected_tokens",
    [
        (
            {"A"},
            "Regional",
            "Desc",
            "2020",
            [
                "inmaterial",
                "tipo a",
                "alcance regional",
                "descripcion: desc",
                "fecha: 2020",
            ],
        ),
        (
            set(),
            None,
            None,
            None,
            [
                "tipologia no especificada",
                "ambito no definido",
                "sin descripcion",
                "fecha no especificada",
            ],
        ),
    ],
)
def test_intangible_asset_str_fallbacks(
    intangible_asset_factory, typology, scope, description, date, expected_tokens
):
    ia = intangible_asset_factory(
        typology=typology,
        scope=scope,
        description=description,
        date=date,
        name="Bien I",
    )
    s = _normalize(str(ia))
    for token in expected_tokens:
        assert token in s
    assert "none" not in s


# ==============================
# MunicipalityInfo.get_embedding_text
# ==============================


def test_embedding_text_includes_core_fields_and_no_none(
    sample_municipality_info_from_dict,
):
    mi = sample_municipality_info_from_dict
    text = _normalize(mi.get_embedding_text())
    # Municipality name appears
    assert "el puerto" in text
    # Capital phrase respects the flag
    assert "que no es capital de provincia." in text
    # Includes description and history
    assert "desc" in text
    assert "hist" in text
    # No literal "None"
    assert "none" not in text


def test_embedding_text_aggregates_real_estate_and_intangible(
    mixed_towns_with_real_estate, mixed_towns_with_intangible
):
    # Town with real estate asset
    t_re = mixed_towns_with_real_estate[0]
    text_re = _normalize(t_re.get_embedding_text())
    assert "realestate" in text_re
    assert "rural" in text_re
    assert "caracterizacion" in text_re
    assert "none" not in text_re

    # Town with intangible asset
    t_in = mixed_towns_with_intangible[0]
    text_in = _normalize(t_in.get_embedding_text())
    assert "festivity" in text_in
    assert "cultural" in text_in or "festive" in text_in  # at least one typology label
    assert "none" not in text_in


def test_embedding_text_over_large_batch_has_content_and_no_none(large_towns_batch):
    # Spot-check a few towns to ensure embedding text is non-empty and safe
    for town in (large_towns_batch[0], large_towns_batch[-1]):
        text = _normalize(town.get_embedding_text())
        assert isinstance(text, str) and text.strip() != ""
        assert "none" not in text


def test_base_towns_fixture_shapes_data(base_towns):
    # Sanity check that the base_towns factory yields correct shape and defaults
    towns = base_towns(n=3, with_images=True)
    assert len(towns) == 3
    for i, t in enumerate(towns):
        assert t.name == f"T{i}"
        assert t.images == [f"http://img/{i}.jpg"]
        # get_embedding_text should always be a non-empty string
        assert _normalize(t.get_embedding_text()).strip() != ""
