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


@router.get("/bootstrap-status", summary="Bootstrap Status")
async def bootstrap_status(session: Annotated[AsyncSession, Depends(get_session)]):
    """
    Returns whether initial data bootstrap has completed.

    Bootstrap is considered ready when the `towns` table exists and at least one
    row has non-null embeddings.
    """

    try:
        total_towns_res = await session.execute(text("SELECT COUNT(*) FROM towns"))
        total_towns = int(total_towns_res.scalar() or 0)

        embedded_towns_res = await session.execute(
            text("SELECT COUNT(*) FROM towns WHERE embeddings IS NOT NULL")
        )
        embedded_towns = int(embedded_towns_res.scalar() or 0)

        is_ready = total_towns > 0 and embedded_towns > 0

        return {
            "ready": is_ready,
            "message": (
                "Bootstrap completed"
                if is_ready
                else "Bootstrap in progress or not executed yet"
            ),
            "counts": {
                "towns": total_towns,
                "embedded_towns": embedded_towns,
            },
        }
    except Exception as e:
        logger.warning(f"Bootstrap status check failed: {e}")
        return {
            "ready": False,
            "message": "Bootstrap not ready yet",
            "counts": {
                "towns": 0,
                "embedded_towns": 0,
            },
        }


router.include_router(itineraryRouter, prefix="/itinerary")
