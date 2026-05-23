from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.core.route_class import StandardAPIRoute
from app.models.user import User
from app.repositories.user import UserRepository
from app.repositories.token_blacklist_repository import TokenBlacklistRepository
from app.schemas.auth_dto import LoginRequest, TokenResponse, RegisterRequest, RegisterResponse, LogoutRequest
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter(route_class=StandardAPIRoute)


_bearer_scheme = HTTPBearer()

def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency factory — matches the pattern used by all other routes."""
    repository = UserRepository(db)
    blacklist_repository = TokenBlacklistRepository(db)
    return AuthService(repository, blacklist_repository)


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


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    """Create a new user account and receive JWT tokens immediately."""
    return await service.register(data)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: LogoutRequest,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """Logout the current user by blacklisting their access and refresh tokens.
    
    The user must be authenticated. The access token is extracted from the Authorization header.
    """
    await service.logout(credentials.credentials, request)
    return {"message": "Successfully logged out"}
