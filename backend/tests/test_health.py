# All code/comments in English
import httpx
import respx
import pytest
from app.config.settings import settings


@pytest.mark.anyio
async def test_health_ok(client, override_db_ok, respx_mock):
    # Mock Valhalla /status as healthy
    respx_mock.get(f"{settings.valhalla_url}/status").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    r = await client.get("/api/v1/health")
    body = r.json()
    assert r.status_code == 200
    assert body["status"] == "ok"
    assert body["database"] == "connected"
    assert body["valhalla"] == "connected"


@pytest.mark.anyio
async def test_health_degraded_db(client, override_db_fail, respx_mock):
    respx_mock.get(f"{settings.valhalla_url}/status").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    r = await client.get("/api/v1/health")
    body = r.json()
    assert body["status"] == "degraded"
    assert body["database"] == "disconnected"
    assert body["valhalla"] == "connected"


@pytest.mark.anyio
async def test_health_degraded_valhalla(client, override_db_ok, respx_mock):
    #  Mock Valhalla /status as unhealthy
    respx_mock.get(f"{settings.valhalla_url}/status").mock(
        return_value=httpx.Response(500)
    )
    r = await client.get("/api/v1/health")
    body = r.json()
    assert body["status"] == "degraded"
    assert body["database"] == "connected"
    assert body["valhalla"] == "disconnected"


@pytest.mark.anyio
async def test_health_degraded_both(client, override_db_fail, respx_mock):
    #  Mock Valhalla /status as unhealthy

    respx_mock.get(f"{settings.valhalla_url}/status").mock(
        return_value=httpx.Response(500)
    )
    r = await client.get("/api/v1/health")
    body = r.json()
    assert body["status"] == "degraded"
    assert body["database"] == "disconnected"
    assert body["valhalla"] == "disconnected"
