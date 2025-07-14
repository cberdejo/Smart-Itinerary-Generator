import os
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

load_dotenv()


def get_async_engine():
    """
    Creates and returns an asynchronous SQLAlchemy engine for connecting to a PostgreSQL database.
    """

    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "mysecretpassword")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "postgres")

    if not all([user, password, host, port, db]):
        raise ValueError("Missing required database environment variables")

    connection_string = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
    return create_async_engine(connection_string, echo=True)


def get_async_session(engine):
    """
    Creates and returns an asynchronous SQLAlchemy session factory bound to the provided engine.
    """
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
