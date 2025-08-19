import numpy as np
from pipeline.tasks import generate_embeddings as mod_embeddings


def test_generate_embeddings_returns_stable_4tuple(
    monkeypatch, base_towns, mock_embeddings
):
    """It must always return a 4-tuple (town_rows, embedding_rows, image_rows, keyword_rows)."""
    towns = base_towns(3)
    monkeypatch.setattr(mod_embeddings, "get_embedding", mock_embeddings)

    out = mod_embeddings.generate_embeddings(towns)
    assert isinstance(out, tuple) and len(out) == 4


def test_generate_embeddings_calls_utils_once_with_n_texts(monkeypatch, base_towns):
    """The get_embedding function from utils is called once with all texts from all towns."""
    towns = base_towns(3)
    calls = {"n": 0}
    captured_texts = []

    def fake_get_embedding(texts):
        calls["n"] += 1
        captured_texts.extend(texts)
        return np.array([[0.0] * 10 for _ in texts])

    monkeypatch.setattr(mod_embeddings, "get_embedding", fake_get_embedding)

    _ = mod_embeddings.generate_embeddings(towns)

    assert calls["n"] == 1
    assert len(captured_texts) == 3  # 3 towns -> 3 texts


def test_generate_embeddings_with_real_estate_assets(
    monkeypatch, mixed_towns_with_real_estate, mock_embeddings
):
    monkeypatch.setattr(mod_embeddings, "get_embedding", mock_embeddings)

    _, _, real_estate_assets, _ = mod_embeddings.generate_embeddings(
        mixed_towns_with_real_estate
    )

    assert len(real_estate_assets) == 1  # only one town has assets
    asset = real_estate_assets[0]
    assert asset.name == "RealEstate"
    assert asset.municipality_ine == "00000"
    assert asset.description == "Description"
    assert asset.characterization == "characterization"
    assert len(asset.typologies) == 1
    assert asset.typologies[0]["den_tipologia"] == "Rural"
    assert asset.typologies[0]["den_etnia"] == "Local"
    assert asset.typologies[0]["periodos"] == "Century XIX"
    assert asset.typologies[0]["denom_acti"] == "Agriculture"


def test_generate_embeddings_with_intangible_assets(
    monkeypatch, mixed_towns_with_intangible, mock_embeddings
):
    monkeypatch.setattr(mod_embeddings, "get_embedding", mock_embeddings)

    _, intangible_assets, _, _ = mod_embeddings.generate_embeddings(
        mixed_towns_with_intangible
    )

    assert len(intangible_assets) == 1  # Solo un town tiene assets
    assert intangible_assets[0].name == "Festivity"
    assert intangible_assets[0].municipality_ine == "00000"
    assert intangible_assets[0].scope == "Municipal"
    assert intangible_assets[0].typology == "Cultural, Festive"
    assert intangible_assets[0].description == "Description"
    assert intangible_assets[0].date == "2025-01-01"


def test_generate_embeddings_with_multiple_images(
    monkeypatch, base_towns, mock_embeddings
):
    towns = base_towns(1)
    towns[0].images = ["http://img/1.jpg", "http://img/2.jpg"]
    monkeypatch.setattr(mod_embeddings, "get_embedding", mock_embeddings)

    _, _, _, images = mod_embeddings.generate_embeddings(towns)

    assert len(images) == 2
    assert {img.url for img in images} == {"http://img/1.jpg", "http://img/2.jpg"}
    assert {img.municipality_ine for img in images} == {"00000"}


def test_generate_embeddings_maps_basic_fields(
    monkeypatch, base_towns, mock_embeddings
):
    """Minimal content sanity: IDs, names and embedding vectors are well formed."""
    towns = base_towns(3)
    monkeypatch.setattr(mod_embeddings, "get_embedding", mock_embeddings)

    town_rows, _, _, _ = mod_embeddings.generate_embeddings(towns)

    # Town rows keep identifiers and names
    assert {r.municipality_ine for r in town_rows} == {"00000", "00001", "00002"}
    assert {r.municipality_name for r in town_rows} == {"T0", "T1", "T2"}


def test_generate_embeddings_collects_image_rows_when_present(
    monkeypatch, base_towns, mock_embeddings
):
    """If towns contain image URLs, they must be flattened into image_rows."""
    towns = base_towns(3, with_images=True)
    monkeypatch.setattr(mod_embeddings, "get_embedding", mock_embeddings)

    town_rows, _, _, images = mod_embeddings.generate_embeddings(towns)

    assert len(town_rows) == 3
    assert len(images) == 3
    for r in images:
        assert r.municipality_ine in {"00000", "00001", "00002"}
        assert r.url.startswith("http://img/")


def test_generate_embeddings_with_optional_fields(
    monkeypatch, base_towns, mock_embeddings
):
    towns = base_towns(1)
    towns[0].province_identifier = None
    towns[0].province_name = None
    monkeypatch.setattr(mod_embeddings, "get_embedding", mock_embeddings)

    town_rows, _, _, _ = mod_embeddings.generate_embeddings(towns)

    assert town_rows[0].province_identifier is None
    assert town_rows[0].province_name is None


def test_generate_embeddings_batch_processing(monkeypatch, large_towns_batch):
    towns = large_towns_batch
    calls = []

    def fake_get_embedding(texts):
        calls.append(len(texts))
        return np.array([[0.0] * 10 for _ in texts])

    monkeypatch.setattr(mod_embeddings, "get_embedding", fake_get_embedding)

    result = mod_embeddings.generate_embeddings(towns)

    assert len(calls) == 2  # It should make 2 calls (32 + 3)
    assert calls[0] == 32
    assert calls[1] == 3
    assert len(result[0]) == 35  # All processed towns


def test_generate_embeddings_error_handling(monkeypatch, large_towns_batch):
    """If a call to get_embedding fails, it must be skipped."""
    towns = large_towns_batch

    def fake_get_embedding(texts):
        if "T1" in texts[1]:  # Error in second call
            raise ValueError("API Error")
        return np.array([[0.0] * 10 for _ in texts])

    monkeypatch.setattr(mod_embeddings, "get_embedding", fake_get_embedding)

    town_rows, _, _, _ = mod_embeddings.generate_embeddings(towns)

    # It should skip the first batch
    assert len(town_rows) == 3
    assert {t.municipality_ine for t in town_rows} == {"00032", "00033", "00034"}
