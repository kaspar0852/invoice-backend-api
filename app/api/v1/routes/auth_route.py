from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.core.route_class import StandardAPIRoute
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth_dto import LoginRequest, TokenResponse
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter(route_class=StandardAPIRoute)


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency factory — matches the pattern used by all other routes."""
    repository = UserRepository(db)
    return AuthService(repository)


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate with email + password and receive JWT tokens."""
    return await service.login(credentials)


@router.get("/me", response_model=UserRead)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    """Return the profile of the currently authenticated user."""
    return UserRead.model_validate(current_user)
