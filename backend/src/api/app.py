from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from helpers.postgres import create_db_and_tables, get_session
from contextlib import asynccontextmanager
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel
from app_config.logger import get_logger
from api.routes import router

logger = get_logger("APP")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for the FastAPI application.
    Handles startup and shutdown events:
    - On startup: Logs the startup process and initializes the database by creating tables.
    - On shutdown: Logs the shutdown process and performs any necessary cleanup.
    Args:
        app (FastAPI): The FastAPI application instance.
    Yields:
        None: Used to signal the lifespan context for FastAPI.
    """

    # Startup
    logger.info("Starting up...")
    create_db_and_tables()
    logger.info("Database tables created")

    yield

    # Shutdown
    logger.info("Shutting down...")
    # Add any cleanup code here if needed
    logger.info("Cleanup completed")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router, prefix="/api/v1")
