# tests/test_get_itinerary.py
# All code/comments in English

import json
import types
import pytest

from app.models.form_response import FormResponse, Location
from app.controllers.get_itinerary import get_itinerary
from app.models.valhalla import Trip, Summary


def make_fake_trip() -> Trip:
    """Return a minimal valid Trip instance for tests."""
    return Trip(
        locations=[],  # empty list is fine for the model
        legs=[],  # empty list is fine for the model
        summary=Summary(
            has_time_restrictions=False,
            has_toll=False,
            has_highway=False,
            has_ferry=False,
            min_lat=0.0,
            min_lon=0.0,
            max_lat=0.0,
            max_lon=0.0,
            time=0.0,
            length=0.0,
            cost=0.0,
        ),
        status_message="Ok",
        status=0,
        units="kilometers",
        language="en",
    )


# --------- Test doubles (minimal shapes that the app expects) ---------


class DummyTown:
    """Minimal Town shape with attributes used by get_itinerary and TownOut."""

    def __init__(self, lat, lng, embeddings, has_beach, name="Town"):
        self.latitude = lat
        self.longitude = lng
        self.embeddings = embeddings
        self.has_beach = has_beach
        self.municipality_ine = "0000"
        self.municipality_name = name
        self.description = None
        self.history = None
        self.capital_city = False
        self.province_identifier = "P"
        self.province_name = "Prov"
        self.images = []
        self.real_estate_assets = []
        self.intangible_assets = []


class FakeResult:
    """Mimic SQLAlchemy AsyncResult with .scalars().all()."""

    def __init__(self, items):
        self._items = items

    def scalars(self):
        return types.SimpleNamespace(all=lambda: self._items)


class FakeSession:
    """Mimic AsyncSession.execute() returning FakeResult."""

    def __init__(self, items):
        self._items = items

    async def execute(self, *_, **__):
        return FakeResult(self._items)


# --------- Helpers ---------


def parse_json_response(resp):
    """Helper to decode JSONResponse into dict."""
    return json.loads(resp.body)


# ================================= TESTS ================================


@pytest.mark.anyio
async def test_itinerary_happy_path(monkeypatch):
    """
    Ensures: with valid data we get 200, a trip object, and 3 towns max.
    """
    from app.controllers import get_itinerary as ctrl

    # Mock embedder to produce a stable vector
    monkeypatch.setattr(ctrl, "get_embedding", lambda _: [1.0, 0.0])

    # Async passthrough isochrone filter
    async def passthrough_filter(_loc, _limit, towns):
        return towns

    monkeypatch.setattr(ctrl, "filter_by_location_polygon", passthrough_filter)

    # Async route mock returning a dummy trip-like object

    async def fake_get_optimal_route(_locations):
        return make_fake_trip()

    monkeypatch.setattr(ctrl, "get_optimal_route", fake_get_optimal_route)

    towns = [
        DummyTown(0, 0, [0.9, 0.1], True, "A"),
        DummyTown(1, 1, [0.8, 0.2], False, "B"),
        DummyTown(2, 2, [0.7, 0.3], True, "C"),
        DummyTown(3, 3, [0.6, 0.4], False, "D"),
    ]
    session = FakeSession(towns)

    form = FormResponse(
        beach="indiference",
        location=Location(lat=36.7, lng=-4.4, label="Málaga"),
        travelTimeLimit=60,
        culturalInfluences=None,
        environment=None,
        historicalPeriods=None,
        monuments=None,
        traditions=None,
        travelInterests=None,
        villageType=None,
    )

    resp = await get_itinerary(form, session)
    assert resp.status_code == 200
    body = parse_json_response(resp)
    assert body["message"] == "Itinerary generated successfully"
    assert body["data"]["trip"] is not None
    assert len(body["data"]["towns"]) == 3
    assert [t["municipality_name"] for t in body["data"]["towns"]] == ["A", "B", "C"]


@pytest.mark.anyio
async def test_itinerary_no_towns_match(monkeypatch):
    """
    Ensures: when filtering by isochrone returns [], we respond with 404 and message.
    """
    from app.controllers import get_itinerary as ctrl

    monkeypatch.setattr(ctrl, "get_embedding", lambda _: [1.0, 0.0])

    # Force isochrone filter to exclude all towns (async!)
    async def empty_filter(_loc, _limit, _towns):
        return []

    monkeypatch.setattr(ctrl, "filter_by_location_polygon", empty_filter)

    session = FakeSession([DummyTown(0, 0, [0.1, 0.9], False, "X")])

    form = FormResponse(
        beach="yes",
        location=Location(lat=0, lng=0, label=None),
        travelTimeLimit=60,
        culturalInfluences=None,
        environment=None,
        historicalPeriods=None,
        monuments=None,
        traditions=None,
        travelInterests=None,
        villageType=None,
    )

    resp = await get_itinerary(form, session)
    assert resp.status_code == 404
    assert b"No towns matched your preferences" in resp.body


@pytest.mark.anyio
async def test_itinerary_not_enough_locations(monkeypatch):
    """
    Ensures: when there is only one town and no starting location, we return 204 and skip routing.
    """
    from app.controllers import get_itinerary as ctrl

    monkeypatch.setattr(ctrl, "get_embedding", lambda _: [1.0, 0.0])

    session = FakeSession([DummyTown(0, 0, [1, 0], True, "Solo")])

    form = FormResponse(
        beach="indiference",
        location=None,  # no start point
        travelTimeLimit=None,
        culturalInfluences=None,
        environment=None,
        historicalPeriods=None,
        monuments=None,
        traditions=None,
        travelInterests=None,
        villageType=None,
    )

    resp = await get_itinerary(form, session)
    assert resp.status_code == 204
    assert b"Not enough locations for optimal route" in resp.body


@pytest.mark.anyio
async def test_itinerary_error_get_optimal_route(monkeypatch):
    """
    Ensures: when routing raises, we return 500 with proper message.
    """
    from app.controllers import get_itinerary as ctrl

    monkeypatch.setattr(ctrl, "get_embedding", lambda _: [1.0, 0.0])

    # Let towns pass through (async!)
    async def passthrough_filter(_loc, _limit, towns):
        return towns

    monkeypatch.setattr(ctrl, "filter_by_location_polygon", passthrough_filter)

    # Make routing fail on await (async!)
    async def boom(_):
        raise RuntimeError("routing down")

    monkeypatch.setattr(ctrl, "get_optimal_route", boom)

    session = FakeSession([DummyTown(0, 0, [1, 0], True, "R1")])

    form = FormResponse(
        beach="indiference",
        location=Location(lat=0, lng=0, label=None),  # ensures >= 2 locations
        travelTimeLimit=60,
        culturalInfluences=None,
        environment=None,
        historicalPeriods=None,
        monuments=None,
        traditions=None,
        travelInterests=None,
        villageType=None,
    )

    resp = await get_itinerary(form, session)
    assert resp.status_code == 500
    assert b"Error getting optimal route" in resp.body


@pytest.mark.anyio
async def test_itinerary_respects_beach_prioritization(monkeypatch):
    """
    When beach='yes', beach towns are prioritized at the top.
    Our FakeSession does not execute SQL WHERE, so inland towns still arrive.
    We ensure the top-2 are beach towns given the embedding setup.
    """
    from app.controllers import get_itinerary as ctrl

    monkeypatch.setattr(ctrl, "get_embedding", lambda _: [1.0, 0.0])

    async def passthrough_filter(_loc, _limit, towns):
        return towns

    monkeypatch.setattr(ctrl, "filter_by_location_polygon", passthrough_filter)

    async def fake_get_optimal_route(_locations):
        return make_fake_trip()

    monkeypatch.setattr(ctrl, "get_optimal_route", fake_get_optimal_route)

    # Beach embeddings close to [1,0]; inland embeddings orthogonal to [1,0]
    towns = [
        DummyTown(0, 0, [0.95, 0.05], True, "Beach-1"),
        DummyTown(1, 1, [0.0, 1.0], False, "Inland-1"),
        DummyTown(2, 2, [0.85, 0.15], True, "Beach-2"),
        DummyTown(3, 3, [0.0, 1.0], False, "Inland-2"),
        DummyTown(2, 2, [0.85, 0.15], True, "Beach-3"),
        DummyTown(3, 3, [0.0, 1.0], False, "Inland-2"),
    ]
    session = FakeSession(towns)

    form = FormResponse(
        beach="yes",
        location=Location(lat=36.7, lng=-4.4, label="Málaga"),
        travelTimeLimit=30,
        culturalInfluences=None,
        environment=None,
        historicalPeriods=None,
        monuments=None,
        traditions=None,
        travelInterests=None,
        villageType=None,
    )

    resp = await get_itinerary(form, session)
    assert resp.status_code == 200
    body = parse_json_response(resp)
    names = [t["municipality_name"] for t in body["data"]["towns"]]

    # The top-3 must be beach towns (order among them doesn't matter)
    assert set(names) == {"Beach-1", "Beach-2", "Beach-3"}


@pytest.mark.anyio
async def test_itinerary_ranking_order(monkeypatch):
    """
    Ensures: ranking respects cosine similarity ordering (descending).
    """
    from app.controllers import get_itinerary as ctrl

    monkeypatch.setattr(ctrl, "get_embedding", lambda _: [1.0, 0.0])

    async def passthrough_filter(_loc, _limit, towns):
        return towns

    monkeypatch.setattr(ctrl, "filter_by_location_polygon", passthrough_filter)

    async def fake_get_optimal_route(_locations):
        return make_fake_trip()

    monkeypatch.setattr(ctrl, "get_optimal_route", fake_get_optimal_route)

    towns = [
        DummyTown(0, 0, [0.1, 0.9], True, "Worst"),
        DummyTown(1, 1, [0.7, 0.3], True, "Mid"),
        DummyTown(2, 2, [0.95, 0.05], True, "Best"),
        DummyTown(3, 3, [0.6, 0.4], True, "Low"),
    ]
    session = FakeSession(towns)

    form = FormResponse(
        beach="indiference",
        location=Location(lat=36.7, lng=-4.4, label="Málaga"),
        travelTimeLimit=45,
        culturalInfluences=None,
        environment=None,
        historicalPeriods=None,
        monuments=None,
        traditions=None,
        travelInterests=None,
        villageType=None,
    )

    resp = await get_itinerary(form, session)
    assert resp.status_code == 200
    body = parse_json_response(resp)
    names = [t["municipality_name"] for t in body["data"]["towns"]]
    assert names == ["Best", "Mid", "Low"]
