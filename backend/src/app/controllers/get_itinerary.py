import numpy as np
from pydantic import ValidationError
from sklearn.metrics.pairwise import cosine_similarity
from sqlmodel import select
from sqlalchemy.orm import selectinload

from models.municiaplity import TownOut
from models.generic_response import GenericResponse
from models.itinerary import Itinerary
from models.form_response import FormResponse, Coordinate
from helpers.valhalla import filter_by_location_polygon, get_optimal_route

from app_config.logger import get_logger
from app_config.db_models import Town
from app_helpers.embedder import get_embedding

logger = get_logger(__name__)


def rank_towns_by_similarity(user_embedding, towns: list[Town]) -> list[Town]:
    """
    Ranks towns based on cosine similarity to the user's embedding vector.

    Args:
         user_emb (np.ndarray): The user's embedding vector.
         towns (list[TownModel]): List of towns to rank.

    Returns:
         list[TownModel]: Sorted list of towns (most similar first).
    """
    try:
        town_vectors = np.array([town.embeddings for town in towns])
        similarities = cosine_similarity([user_embedding], town_vectors)[0]
        sorted_towns = sorted(zip(towns, similarities), key=lambda x: -x[1])
        return [town for town, _ in sorted_towns]
    except Exception as e:
        logger.error(f"Error calculating similarity: {e}")
        return towns  # fallback


async def get_itinerary(form_data: FormResponse, db_session) -> GenericResponse:
    """
    Generates a personalized itinerary based on user preferences and real driving times.

    The process includes:
    1. Filtering towns (e.g., beach preference, isochrone reachability).
    2. Getting top 3 ranked towns by embedding similarity.
    3. Generating optimized route using Valhalla.

    Args:
        formData (FormResponse): User input with preferences and optional location.
        db_session: SQLAlchemy async session.

    Returns:
        GenericResponse: A standard API response with itinerary data.
    """
    response = GenericResponse(
        code=500, message="Something went wrong generating itinerary", data=[]
    )

    try:
        # Step 1: Filter towns from DB based on form
        query = select(Town).options(
            selectinload(Town.images),
            selectinload(Town.intangible_assets),
            selectinload(Town.real_estate_assets),
        )

        if form_data.beach and form_data.beach != "indiference":
            query = query.where(Town.has_beach == (form_data.beach == "yes"))

        result = await db_session.execute(query)
        towns = result.scalars().all()

        # Optional: filter by Valhalla isochrone
        if form_data.location and form_data.travelTimeLimit:
            try:
                towns = await filter_by_location_polygon(
                    form_data.location, form_data.travelTimeLimit, towns
                )
            except:
                logger.warning(
                    "Valhalla isochrone filtering failed, proceeding without location filtering"
                )

        # Step 2: Rank towns using semantic similarity
        form_embedding = get_embedding(form_data.get_embedding_text())
        ranked_towns = rank_towns_by_similarity(form_embedding, towns)
        top_towns = ranked_towns[:3]

        if not top_towns:
            response.code = 404
            response.message = "No towns matched your preferences"
            return response.to_json_response()

        # Step 3: Define starting point
        all_locations = []
        if form_data.location:
            all_locations = [form_data.location] + [
                Coordinate(lat=town.latitude, lng=town.longitude) for town in top_towns
            ]
        else:
            first = top_towns[0]

            start_coord = Coordinate(lat=first.latitude, lng=first.longitude)
            all_locations = [start_coord] + [
                Coordinate(lat=town.latitude, lng=town.longitude)
                for town in top_towns[1:]
            ]
        try:
            trip = await get_optimal_route(all_locations)
        except Exception as e:
            logger.error(f"Error getting optimal route: {e}")
            response.code = 500
            response.message = "Error getting optimal route"
            return response.to_json_response()

        # Final response
        response.code = 200
        response.message = "Itinerary generated successfully"
        response.data = Itinerary(
            trip=trip, towns=[TownOut.model_validate(town) for town in top_towns]
        )

    except ValidationError as ve:
        response.code = 400
        response.message = str(ve)

    except Exception as e:
        logger.exception("Unexpected error in itinerary generation")
        response.code = 500
        response.message = str(e)

    return response.to_json_response()
