"""
Main API router for the application.

This module sets up the primary FastAPI router, includes sub-routers for different API endpoints,
and provides utility endpoints such as health checks. All API routes should be registered here
either directly or via sub-routers.
"""

from typing import Annotated

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text

from app_config.logger import get_logger
from app.config.settings import settings
from app.helpers.db import get_session
from app.routes.itinerary import router as itineraryRouter

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


router.include_router(itineraryRouter, prefix="/itinerary")
