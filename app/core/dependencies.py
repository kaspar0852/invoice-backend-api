from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import SessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to retrieve the database session."""
    async with SessionLocal() as session:
        yield session
