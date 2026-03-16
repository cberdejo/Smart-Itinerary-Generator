import numpy as np
from pydantic import ValidationError
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlmodel import select
from sqlalchemy.orm import selectinload

from app.models.municiaplity import TownOut
from app.models.generic_response import GenericResponse
from app.models.itinerary import Itinerary
from app.models.form_response import FormResponse, Coordinate
from app.helpers.valhalla import filter_by_location_polygon, get_optimal_route

from app.config.logger import get_logger
from app.models.db_models import Town
from app.helpers.embedder import get_embedding, rerank_documents
from app.helpers.hybrid_search import build_search_texts_from_towns

logger = get_logger(__name__)


def rank_towns_by_similarity(
    user_embedding, query_text: str, towns: list[Town], use_rerank: bool = True
) -> list[Town]:
    """
    Ranks towns with hybrid retrieval:
      1) Dense semantic similarity (embeddings)
      2) Sparse lexical similarity (TF-IDF cosine)
      3) Reciprocal Rank Fusion
      4) Optional CrossEncoder reranking

    Args:
         user_embedding (np.ndarray): User embedding vector.
         query_text (str): Raw query text built from user form.
         towns (list[Town]): Candidate towns.
         use_rerank (bool): Whether to rerank top fused candidates.

    Returns:
         list[Town]: Sorted list of towns (most relevant first).
    """
    try:
        if not towns:
            return []

        query_text = (query_text or "").strip()

        # Dense scores
        dense_scores = []
        for town in towns:
            if town.embeddings is None:
                dense_scores.append(0.0)
                continue
            score = cosine_similarity([user_embedding], [town.embeddings])[0][0]
            dense_scores.append(float(score))

        # Sparse scores
        town_documents = build_search_texts_from_towns(towns)
        try:
            vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2))
            matrix = vectorizer.fit_transform([query_text] + town_documents)
            sparse_scores = cosine_similarity(matrix[0:1], matrix[1:]).flatten().tolist()
        except Exception as sparse_error:
            logger.warning(f"Sparse scoring failed, fallback to dense-only: {sparse_error}")
            sparse_scores = [0.0] * len(towns)

        dense_rank = sorted(range(len(towns)), key=lambda i: dense_scores[i], reverse=True)
        sparse_rank = sorted(
            range(len(towns)), key=lambda i: sparse_scores[i], reverse=True
        )

        # Reciprocal Rank Fusion
        rrf_k = 60
        fused_scores = [0.0] * len(towns)
        for rank_position, town_idx in enumerate(dense_rank):
            fused_scores[town_idx] += 1.0 / (rrf_k + rank_position + 1)
        for rank_position, town_idx in enumerate(sparse_rank):
            fused_scores[town_idx] += 1.0 / (rrf_k + rank_position + 1)

        fused_rank = sorted(
            range(len(towns)), key=lambda i: fused_scores[i], reverse=True
        )

        if use_rerank and fused_rank:
            top_n = min(15, len(fused_rank))
            top_indices = fused_rank[:top_n]
            top_docs = [town_documents[i] for i in top_indices]

            try:
                rerank_scores = rerank_documents(query_text, top_docs)
                reranked_top = [
                    idx
                    for idx, _ in sorted(
                        zip(top_indices, rerank_scores),
                        key=lambda pair: pair[1],
                        reverse=True,
                    )
                ]
                remaining = [idx for idx in fused_rank if idx not in set(top_indices)]
                fused_rank = reranked_top + remaining
            except Exception as rerank_error:
                logger.warning(f"Reranking failed, keeping fused order: {rerank_error}")

        return [towns[i] for i in fused_rank]
    except Exception as e:
        logger.error(f"Error calculating hybrid ranking: {e}")
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

        # Step 2: Hybrid retrieval + reranking
        query_text = form_data.get_embedding_text().strip()
        dense_query_text = query_text if query_text else "pueblos de andalucia"
        form_embedding = get_embedding(dense_query_text)
        ranked_towns = rank_towns_by_similarity(
            form_embedding,
            query_text=dense_query_text,
            towns=towns,
            use_rerank=True,
        )
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
            all_locations = [
                Coordinate(lat=town.latitude, lng=town.longitude) for town in top_towns
            ]

        if len(all_locations) < 2:
            logger.error("Not enough locations for optimal route")
            response.data = Itinerary(
                trip=None, towns=[TownOut.model_validate(town) for town in top_towns]
            )
            response.code = 204
            response.message = "Not enough locations for optimal route"
            return response.to_json_response()

        try:
            trip = await get_optimal_route(all_locations)
        except Exception as e:
            logger.error(f"Error getting optimal route: {e}")
            response.code = 500
            response.message = "Error getting optimal route"
            return response.to_json_response()

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
