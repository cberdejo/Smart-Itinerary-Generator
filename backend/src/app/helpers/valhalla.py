import httpx
from models.form_response import Coordinate
from models.valhalla import Trip
from shapely.geometry import Point, Polygon
from app_config.db_models import Town
from app_config.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)


async def filter_by_location_polygon(
    coords: Coordinate, minutes: int, towns: list[Town]
) -> list[Town]:
    """
    Filters towns that are reachable within 60 minutes using Valhalla isochrone service.

    Args:
         coords (Location): User's location coordinates.
         towns (list[TownModel]): List of towns to filter.

    Returns:
         list[TownModel]: Towns inside the isochrone polygon.
    """

    # ask valhalla to get isocrone de 60 minutes
    payload = {
        "locations": [{"lat": coords.lat, "lon": coords.lng}],
        "costing": "auto",
        "contours": [{"time": minutes}],
        "polygons": True,
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.valhalla_url}/isochrone", json=payload, timeout=10
            )
            response.raise_for_status()
            polygon_coords = response.json()["features"][0]["geometry"]["coordinates"][
                0
            ]
            polygon = Polygon(polygon_coords)
    except Exception as e:
        logger.error(f"Valhalla error: {e}")
        return []

    return [
        town for town in towns if polygon.contains(Point(town.longitude, town.latitude))
    ]


async def get_optimal_route(locations: list[Coordinate]) -> Trip:
    payload = {
        "locations": [{"lat": loc.lat, "lon": loc.lng} for loc in locations],
        "costing": "auto",
        "units": "kilometers",
    }

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{settings.valhalla_url}/optimized_route", json=payload, timeout=10
            )
            res.raise_for_status()
            trip_data = res.json().get("trip")
            if not trip_data:
                raise ValueError("No trip data found in Valhalla response")

            return Trip(**trip_data)

    except Exception as e:
        logger.error(f"Valhalla error: {e}")
        return None
