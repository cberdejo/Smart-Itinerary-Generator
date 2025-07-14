from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


from api.controllers.get_itinerary import get_itinerary
from models.form_response import FormResponse
from api.dependencies import get_db
from app_config.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", summary="Health Check")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint to verify the API and database are running.

    Returns:
        dict: Status information
    """
    try:
        await db.execute(text("SELECT 1"))
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
    form_data: FormResponse, db: AsyncSession = Depends(get_db)
):
    """
    Generate a travel itinerary based on form data.

    Args:
        form_data: Form response data
        db: Database session

    Returns:
        Generated itinerary
    """
    try:
        return await get_itinerary(form_data, db)
    except Exception as e:
        logger.error(f"Error generating itinerary: {e}")
        raise HTTPException(status_code=500, detail="Error generating itinerary")
