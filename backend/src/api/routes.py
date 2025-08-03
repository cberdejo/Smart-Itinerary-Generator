from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, text
from typing import Annotated

from api.controllers.get_itinerary import get_itinerary
from helpers.postgres import get_session
from models.form_response import FormResponse
from app_config.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", summary="Health Check")
async def health_check(session: Annotated[Session, Depends(get_session)]):  # Fixed typo
    """
    Health check endpoint to verify the API and database are running.

    Returns:
        dict: Status information
    """
    try:
        # If using sync session, don't use await
        session.execute(text("SELECT 1"))
        return {"status": "ok", "message": "API is running", "database": "connected"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "degraded",
            "message": "API is running but database connection failed",
            "database": "disconnected",
        }


@router.post("/itinerary", summary="Generate Itinerary")
async def generate_itinerary(
    form_data: FormResponse, session: Annotated[Session, Depends(get_session)]
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
