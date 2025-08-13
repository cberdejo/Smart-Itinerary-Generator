import types
import pytest
import respx
import httpx
from typing import AsyncGenerator
from fastapi import FastAPI
from app.application import app as fastapi_app
from app.helpers.db import get_session
from httpx import ASGITransport


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def app() -> FastAPI:
    return fastapi_app


@pytest.fixture
async def client(app: FastAPI):
    """
    Async HTTP client against the ASGI app using ASGITransport.
    Compatible with httpx>=0.24 where AsyncClient(app=...) was removed.
    """
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as ac:
        yield ac


@pytest.fixture
def respx_mock():
    """
    Fixture providing a `respx` mock instance for testing purposes.
    """
    with respx.mock(assert_all_called=False) as mock:
        yield mock


# ---- DB override helper ----
class FakeAsyncResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return types.SimpleNamespace(all=lambda: self._items)


class FakeAsyncSessionOK:
    async def execute(self, *args, **kwargs):
        return FakeAsyncResult(items=[1])


class FakeAsyncSessionFail:
    async def execute(self, *args, **kwargs):
        raise RuntimeError("DB failure")


@pytest.fixture
def override_db_ok(app: FastAPI):
    """
    Temporarily override the DB dependency to return a successful result.
    """

    async def _get() -> AsyncGenerator[FakeAsyncSessionOK, None]:
        yield FakeAsyncSessionOK()

    app.dependency_overrides[get_session] = _get
    yield
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture
def override_db_fail(app: FastAPI):
    """
    Temporarily override the DB dependency to return a failed result.
    """

    async def _get() -> AsyncGenerator[FakeAsyncSessionFail, None]:
        yield FakeAsyncSessionFail()

    app.dependency_overrides[get_session] = _get
    yield
    app.dependency_overrides.pop(get_session, None)
