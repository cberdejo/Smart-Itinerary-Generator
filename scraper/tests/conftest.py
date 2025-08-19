import httpx
import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from sqlmodel import SQLModel, Session
import contextlib
from app_config.db_models import Town
from models.municipality import (
    MunicipalityInfo,
    RealEstateAsset,
    IntangibleAsset,
    RealEstateTypology,
)
from types import SimpleNamespace
import pipeline.tasks.upload_report as mod

@contextlib.contextmanager
def temp_attr(module, name, value):
    """Temporarily set module.<name> to value during the context."""
    sentinel = object()
    old = getattr(module, name, sentinel)
    setattr(module, name, value)
    try:
        yield
    finally:
        if old is sentinel:
            delattr(module, name)
        else:
            setattr(module, name, old)


# ------------------------- Database Fixtures ------------------------- #
@pytest.fixture
def sqlite_session():
    from sqlalchemy import create_engine, JSON

    engine = create_engine("sqlite:///:memory:")

    # Local override: swap type before creating metadata

    Town.__table__.c.embeddings.type = JSON()

    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


# ------------------------- HTTP Testing Fixtures ------------------------- #


@pytest.fixture
def mock_response():
    class _MockResponse:
        def __init__(self, status_code=200, json_data=None, html_content=""):
            self.status_code = status_code
            self._json_data = json_data or {}
            self.text = html_content

        def raise_for_status(self):
            if self.status_code != 200:
                req = httpx.Request("GET", "http://example.com")
                resp = httpx.Response(self.status_code, request=req)
                raise httpx.HTTPStatusError("Error", request=req, response=resp)

        def json(self):
            return self._json_data

    return _MockResponse


@pytest.fixture
def mock_requests():
    """Mock for requests.get"""

    class MockRequests:
        @staticmethod
        def get(url, headers=None):
            return _Resp(200, andalusia_sample_data())

    return MockRequests


@pytest.fixture
def mock_async_client(mock_response):
    class _MockAsyncClient:
        def __init__(self, responses=None):
            self.responses = responses or []
            self.calls = []

        async def get(self, url):
            self.calls.append(url)
            if self.responses:
                return self.responses.pop(0)
            return mock_response(404)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    return _MockAsyncClient


@pytest.fixture
def mock_requests_error():
    """Mock for failed requests.get"""

    class MockRequests:
        @staticmethod
        def get(url, headers=None):
            return _BadResp(500)

    return MockRequests


# ------------------------- Data Generation Fixtures ------------------------- #
@pytest.fixture
def sample_town_model():
    def _factory(n=3):
        towns = []
        for i in range(n):
            towns.append(
                Town(
                    municipality_ine=f"{i:05d}",
                    municipality_name="T{i}",
                    description="Test description",
                    province_identifier="1",
                )
            )
        return towns

    return _factory


@pytest.fixture
def sample_municipality_info_data_as_dict():
    return {
        "municipality_name": "El Puerto",
        "municipality_ine": 11027,
        "capital_city": False,
        "latitude": 36.6,
        "longitude": -6.2,
        "description": "desc",
        "history": "hist",
        "images": ["http://img/1.jpg"],
        "province_identifier": 11,
        "province_name": "Cádiz",
    }


@pytest.fixture
def base_towns():
    """Fixture to generate basic town data"""

    def _factory(n=3, with_images=False):
        towns = []
        for i in range(n):
            towns.append(
                MunicipalityInfo(
                    name=f"T{i}",
                    description="d",
                    history="h",
                    images=([f"http://img/{i}.jpg"] if with_images else []),
                    ine=f"{i:05d}",
                    capital=False,
                    latitude=0.0,
                    longitude=0.0,
                    has_beach=False,
                    real_estate_assets=[],
                    intangible_assets=[],
                    province_identifier=1,
                    province_name="X",
                )
            )
        return towns

    return _factory


@pytest.fixture
def mixed_towns_with_real_estate(base_towns):
    """Town with real estate assets"""
    towns = base_towns(2)
    towns[0].real_estate_assets = [
        RealEstateAsset(
            name="RealEstate",
            municipality_name="T0",
            description="Description",
            typologies=[
                RealEstateTypology(
                    den_tipologia="Rural",
                    den_etnia="Local",
                    periodos="Century XIX",
                    denom_acti="Agriculture",
                )
            ],
            characterization="characterization",
        )
    ]
    return towns


@pytest.fixture
def mixed_towns_with_intangible(base_towns):
    """Town with intangible assets"""
    towns = base_towns(2)
    towns[0].intangible_assets = [
        IntangibleAsset(
            name="Festivity",
            municipality_name="T0",
            scope="Municipal",
            typology={"Cultural", "Festive"},
            description="Description",
            date="2025-01-01",
        )
    ]
    return towns


@pytest.fixture
def large_towns_batch(base_towns):
    """Large batch of towns for batch processing tests"""
    return base_towns(35)


@pytest.fixture
def real_estate_asset_factory():
    """Factory for creating RealEstateAsset instances"""

    def factory(**overrides):
        defaults = {
            "name": "Test Property",
            "municipality_name": "Test Town",
            "description": None,
            "typologies": [RealEstateTypology(den_tipologia="Test")],
            "characterization": None,
        }
        return RealEstateAsset(**{**defaults, **overrides})

    return factory


@pytest.fixture
def intangible_asset_factory():
    """Factory for creating IntangibleAsset instances"""

    def factory(**overrides):
        defaults = {
            "name": "Test Event",
            "municipality_name": "Test Town",
            "scope": "Local",
            "typology": {"Cultural"},
            "description": None,
            "date": None,
        }
        return IntangibleAsset(**{**defaults, **overrides})

    return factory


@pytest.fixture
def sample_municipality_info_from_dict(sample_municipality_info_data_as_dict):
    """
    Build a MunicipalityInfo instance from the provided dict fixture,
    mapping field names and setting sensible defaults for required fields not present.
    """
    data = sample_municipality_info_data_as_dict
    return MunicipalityInfo(
        name=data["municipality_name"],
        description=data["description"],
        history=data["history"],
        images=data["images"],
        ine=str(data["municipality_ine"]),
        capital=data["capital_city"],
        latitude=float(data["latitude"]),
        longitude=float(data["longitude"]),
        has_beach=False,  # not in dict, default to False
        real_estate_assets=[],
        intangible_assets=[],
        province_identifier=int(data["province_identifier"]),
        province_name=data["province_name"],
    )


# ------------------------- IAPH Data Fixtures ------------------------- #
@pytest.fixture
def sample_inmaterial_data():
    return {
        "identifica": {"denominacion": "Test Event", "municipio": "Test City"},
        "clob": {"descripcion": "Test description"},
        "tipologiaList": {
            "tipologia": [{"den_tipologia": "Cultural"}, {"den_tipologia": "Festive"}]
        },
    }


@pytest.fixture
def iaph_assets(real_estate_asset_factory, intangible_asset_factory):
    return {
        "real_estate_assets": [
            real_estate_asset_factory(
                name="Castle",
                municipality_name="El Puerto",
                typologies=[RealEstateTypology(den_tipologia="fortress")],
            )
        ],
        "intangible": [
            intangible_asset_factory(name="Event", municipality_name="El Puerto")
        ],
    }


# ------------------------- Mock Services ------------------------- #


@pytest.fixture
def mock_driver_manager():
    with patch("webdriver_manager.chrome.ChromeDriverManager") as mock:
        mock.return_value.install.return_value = "/fake/path/to/chromedriver"
        yield mock


@pytest.fixture
def mock_selenium_driver():
    """Fixture providing a mock WebDriver instance"""
    driver = MagicMock()
    driver.session_id = "mock_session_id"
    driver.find_element.return_value = MagicMock()
    driver.find_elements.return_value = []
    driver.execute_script.return_value = None
    driver.service = MagicMock()
    driver.service.is_connectable.return_value = True
    return driver


@pytest.fixture
def mock_selenium_driver_no_session():
    """Fixture providing a mock WebDriver with no session"""
    driver = MagicMock()
    driver.session_id = None
    driver.service = MagicMock()
    driver.service.is_connectable.return_value = True
    return driver


@pytest.fixture
def mock_embeddings():
    def _mock(texts):
        return np.array([[0.0] * 10 for _ in texts])

    return _mock


@pytest.fixture
def mock_all_tasks():
    """Fixture que mockea todas las dependencias del flujo principal"""
    with (
        patch("pipeline.main.get_municipality_name_and_ubi") as mock_towns,
        patch("pipeline.main.get_towns_info_from_turismo_andalucia") as mock_enrich,
        patch("pipeline.main.get_towns_with_beaches_from_wikipedia") as mock_beaches,
        patch("pipeline.main.get_info_from_iaph") as mock_iaph,
        patch("pipeline.main.build_municipality_info_list") as mock_merge,
        patch("pipeline.main.generate_embeddings") as mock_embeddings,
        patch("pipeline.main.load_info_to_postgres") as mock_save,
        patch("pipeline.main.save_task_metadata_to_minio") as mock_upload,
    ):
        mock_towns.return_value = []
        mock_enrich.return_value = []
        mock_beaches.return_value = {}
        mock_iaph.return_value = {}
        mock_merge.return_value = []
        mock_embeddings.return_value = ([], [], [], [])

        mock_beaches.submit.return_value.result.return_value = {}
        mock_iaph.submit.return_value.result.return_value = {}
        mock_upload.submit.return_value.result.return_value = None

        yield {
            "get_towns": mock_towns,
            "enrich_towns": mock_enrich,
            "get_beaches": mock_beaches,
            "get_iaph": mock_iaph,
            "merge_data": mock_merge,
            "generate_embeddings": mock_embeddings,
            "save_data": mock_save,
            "upload_report": mock_upload,
        }


@pytest.fixture
def fake_minio_settings():
    """Fixture providing fake MinIO settings."""
    return FakeMinioSettings()


@pytest.fixture
def fake_minio():
    """Fixture providing a fresh FakeMinio instance."""
    return FakeMinio()


@pytest.fixture
def fake_minio_class():
    """Fixture returning the FakeMinio *class* (for patching `Minio`)."""
    return FakeMinio


@pytest.fixture
def fake_context(monkeypatch):
    """
    Patch Prefect's `get_run_context` to return a dummy flow_run_id.
    Usage: ctx = fake_context("flow-123")
    """

    def _patch(flow_run_id="flow-123"):
        ctx = SimpleNamespace(task_run=SimpleNamespace(flow_run_id=flow_run_id))
        monkeypatch.setattr(mod, "get_run_context", lambda: ctx)
        return ctx

    return _patch


@pytest.fixture
def patch_minio(monkeypatch, fake_minio):
    """
    Patch upload_report.py to use a FakeMinio.
    Returns the fake_minio instance so tests can inspect put_calls.
    """
    monkeypatch.setattr(mod, "get_minio", lambda: fake_minio)
    monkeypatch.setattr(mod, "setup_minio_buckets", lambda _c: None)
    return fake_minio


# ------------------------- Helper Classes ------------------------- #
class _Resp:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        return self._json

    def raise_for_status(self):
        pass


class _BadResp:
    def __init__(self, status_code=500):
        self.status_code = status_code

    def json(self):
        return {}

    def raise_for_status(self):
        raise Exception(f"HTTP Error {self.status_code}")


def andalusia_sample_data():
    return [
        {
            "province_identifier": 29,
            "municipality_name": "Ronda",
            "municipality_ine": "29067",
            "capital_city": False,
            "latitude": "36,742",
            "longitude": "-5,163",
            "identifier": "foo1",
        },
        {
            "province_identifier": 28,
            "municipality_name": "Getafe",
            "municipality_ine": "28065",
            "capital_city": True,
            "latitude": "40,3",
            "longitude": "-3,73",
            "identifier": "foo2",
        },
    ]


class FakeMinioSettings:
    """Minimal test double mirroring helpers.minio.Settings attributes."""

    minio_url = "localhost:9000"
    minio_user = "minio"
    minio_password = "minio123"
    minio_secure = False


class FakeMinio:
    """
    Mock MinIO client with basic bucket methods for testing.
    """

    def __init__(
        self,
        endpoint="localhost:9000",
        access_key="minio",
        secret_key="minio123",
        secure=False,
    ):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.secure = secure
        self.created = []
        self.bucket_exists = MagicMock()
        self.make_bucket = MagicMock(side_effect=self._make_bucket)

        # store put_object calls
        self.put_calls = []

    def _make_bucket(self, name):
        self.created.append(name)

    def put_object(self, bucket_name, object_name, data, length, content_type):
        """Capture put_object calls for assertions."""
        self.put_calls.append(
            {
                "bucket_name": bucket_name,
                "object_name": object_name,
                "data": data.read(),
                "length": length,
                "content_type": content_type,
            }
        )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
