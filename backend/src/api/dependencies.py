from typing import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to provide a database session.

    Args:
        request (Request): The FastAPI request object.

    Yields:
        AsyncGenerator[AsyncSession, None]: The database session.
    """
    SessionLocal = request.app.state.SessionLocal

    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
