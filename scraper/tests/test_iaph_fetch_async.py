import pytest
from pipeline.tasks.get_info_from_iaph import (
    fetch_single_bien_async,
    get_full_assets_data_async,
    trim_inmaterial,
)


@pytest.mark.asyncio
async def test_fetch_single_bien_async_retries_on_503_then_succeeds(
    mock_async_client, mock_response
):
    """Test retry mechanism on 503 error"""
    client = mock_async_client(
        responses=[mock_response(503), mock_response(200, {"ok": True})]
    )

    result = await fetch_single_bien_async(client, "inmueble", "123", retries=2)

    assert result == {"ok": True}
    assert len(client.calls) == 2
    assert "inmueble/123" in client.calls[-1]


def test_trim_inmaterial_extracts_typology(sample_inmaterial_data):
    """Test typology extraction from intangible asset"""
    result = trim_inmaterial(sample_inmaterial_data)
    assert result.typology == {"Cultural", "Festive"}


@pytest.mark.asyncio
async def test_get_full_assets_data_async_combines_data(
    mock_async_client, mock_response, monkeypatch
):
    """Test data combination from base and detail endpoints"""
    mock_base_data = {"inmueble": [{"id": "1", "denominacion": "A", "municipio": "M"}]}
    client = mock_async_client(responses=[mock_response(200, mock_base_data)])

    async def mock_fetch(*args, **kwargs):
        return {
            "identifica": {"denominacion": "A", "municipio": "M"},
            "clob": {"descripcion": ""},
            "tipologiaList": {"tipologia": []},
        }

    monkeypatch.setattr(
        "pipeline.tasks.get_info_from_iaph.fetch_single_bien_async", mock_fetch
    )
    monkeypatch.setattr(
        "pipeline.tasks.get_info_from_iaph.httpx.AsyncClient",
        lambda *args, **kwargs: client,
    )

    result = await get_full_assets_data_async("inmueble")

    assert len(result) == 1
    assert result[0]["identifica"]["denominacion"] == "A"
    assert "dataset/bien/inmueble" in client.calls[0]


@pytest.mark.asyncio
async def test_get_full_assets_empty_base(
    mock_async_client, mock_response, monkeypatch
):
    """Test empty base data handling"""
    client = mock_async_client(responses=[mock_response(200, {"inmueble": []})])
    monkeypatch.setattr(
        "pipeline.tasks.get_info_from_iaph.httpx.AsyncClient",
        lambda *args, **kwargs: client,
    )

    result = await get_full_assets_data_async("inmueble")
    assert result == []


@pytest.mark.asyncio
async def test_get_full_assets_fallback_to_stub(
    mock_async_client, mock_response, monkeypatch
):
    """Test fallback to stub when detail fetch fails"""
    mock_base_data = {"inmueble": [{"id": "1", "denominacion": "A", "municipio": "M"}]}
    client = mock_async_client(
        responses=[mock_response(200, mock_base_data), mock_response(404)]
    )

    monkeypatch.setattr(
        "pipeline.tasks.get_info_from_iaph.httpx.AsyncClient",
        lambda *args, **kwargs: client,
    )

    result = await get_full_assets_data_async("inmueble")
    assert len(result) == 1
    assert result[0]["identifica"]["denominacion"] == "A"
    assert result[0]["identifica"]["municipio"] == "M"
