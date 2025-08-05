from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.controllers.get_itinerary import get_itinerary
from app.helpers.db import get_session
from app.models.form_response import FormResponse
from app_config.logger import get_logger


logger = get_logger(__name__)

router = APIRouter()


@router.post("/", summary="Generate Itinerary")
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
