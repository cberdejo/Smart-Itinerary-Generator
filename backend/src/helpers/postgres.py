from config.settings import settings
from sqlmodel import SQLModel

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


async_engine = create_async_engine(settings.pguri, echo=True, future=True)
async_session = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


async def create_db_and_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
