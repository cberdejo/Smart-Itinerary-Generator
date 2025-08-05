from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from api.controllers.get_itinerary import get_itinerary
from helpers.postgres import get_session
from models.form_response import FormResponse
from app_config.logger import get_logger
from config.settings import settings
import httpx

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", summary="Health Check")
async def health_check(session: Annotated[AsyncSession, Depends(get_session)]):
    """
    Health check endpoint to verify the API, database, and Valhalla service are running.

    Returns:
        dict: Status information
    """
    db_status = "connected"
    valhalla_status = "connected"

    # Check database
    try:
        await session.execute(text("SELECT 1"))
        await session.commit()

    except Exception as e:
        db_status = "disconnected"
        logger.error(f"Database health check failed: {e}")

    # Check Valhalla
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{settings.valhalla_url}/status", timeout=3)
            res.raise_for_status()
    except Exception as e:
        valhalla_status = "disconnected"
        logger.error(f"Valhalla health check failed: {e}")

    status = (
        "ok"
        if db_status == "connected" and valhalla_status == "connected"
        else "degraded"
    )
    message = "API is running"
    if status == "degraded":
        message += " but some dependencies failed"

    return {
        "status": status,
        "message": message,
        "database": db_status,
        "valhalla": valhalla_status,
    }


@router.post("/itinerary", summary="Generate Itinerary")
async def generate_itinerary(
    form_data: FormResponse, session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Generate a travel itinerary based on form data.

    Args:
        form_data: Form response data
        session: Database session

    Returns:
        Generated itinerary
    """
    try:
        return await get_itinerary(form_data, session)
    except Exception as e:
        logger.error(f"Error generating itinerary: {e}")
        raise HTTPException(status_code=500, detail="Error generating itinerary")
