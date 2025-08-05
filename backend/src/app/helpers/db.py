from typing import AsyncGenerator
from app.config.settings import settings
from sqlmodel import SQLModel

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


async_engine = create_async_engine(settings.pguri, echo=True, future=True)
async_session = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db() -> None:
    """
    Initializes the database by creating all tables defined in the SQLModel metadata.
    This asynchronous function establishes a connection to the database using the async engine,
    and runs the table creation statements. It should be called at application startup to ensure
    that the database schema is up to date.
    Returns:
        None
    """

    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Asynchronous generator that provides a database session.
    Yields:
        AsyncSession: An instance of the asynchronous database session.
    Usage:
        Use this function as a dependency in async contexts to interact with the database.
        Ensures proper opening and closing of the session.
    """

    async with async_session() as session:
        yield session
