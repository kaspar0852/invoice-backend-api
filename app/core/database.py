from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Determine if echo is needed
is_dev = settings.ENVIRONMENT == "development"

# Create the async engine
engine = create_async_engine(
    settings.async_database_url,
    echo=is_dev,
    future=True,
)

# Create the async session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# Declarative base class for models
class Base(DeclarativeBase):
    pass
