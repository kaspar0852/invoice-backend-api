import uuid
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user import UserRepository

# Reusable bearer-token extractor — reads the Authorization: Bearer <token> header
_bearer_scheme = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to retrieve the database session."""
    async with SessionLocal() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency that validates the JWT and returns the authenticated User.

    Raises HTTP 401 when the token is missing, invalid, or expired.
    Raises HTTP 403 when the account is inactive.
    Inject this into any route that requires authentication.
    """
    payload = decode_token(credentials.credentials)

    user_id_raw = payload.get("sub")
    try:
        user_id = uuid.UUID(user_id_raw)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    repository = UserRepository(db)
    user = await repository.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    return user
