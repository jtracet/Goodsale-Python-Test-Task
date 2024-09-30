import logging
from typing import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import get_app_settings

logger = logging.getLogger(__name__)

settings = get_app_settings()

async_engine = create_async_engine(settings.DB_URL, future=True, echo=settings.SQL_SHOW_QUERY)

Session = sessionmaker(  # type: ignore
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with Session() as session:
        try:
            yield session
        except SQLAlchemyError as exc:
            await session.rollback()
            logger.error("Get sqlalchemy error")
            raise exc
