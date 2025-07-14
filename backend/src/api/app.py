from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from helpers.postgres import get_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker

from app_config.logger import get_logger
from api.routes import router

logger = get_logger("APP")


async def lifespan(app: FastAPI):
    """
    Lifecycle event handler for the FastAPI application.

    Args:
        app (FastAPI): The FastAPI application instance .
    """
    logger.info("Initializing DB connection…")
    engine = get_async_engine()
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    app.state.engine = engine
    app.state.SessionLocal = SessionLocal

    logger.info("Finished connecting to DB")
    try:
        yield
    finally:
        await engine.dispose()
        logger.info("Disposed engine")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router, prefix="/api/v1")
