from fastapi import HTTPException, status

from app.repositories.user import UserRepositoryInterface
from app.schemas.auth_dto import LoginRequest, TokenResponse
from app.core.security import verify_password, create_access_token, create_refresh_token


class AuthService:
    def __init__(self, repository: UserRepositoryInterface):
        self.repository = repository

    async def login(self, credentials: LoginRequest) -> TokenResponse:
        """Authenticate a user and return access + refresh tokens.

        Deliberately returns the same 401 error for both "email not found"
        and "wrong password" to avoid user enumeration attacks.
        """
        user = await self.repository.get_by_email(credentials.email)

        # Reject if user doesn't exist or password doesn't match
        if not user or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )

        subject = str(user.id)

        return TokenResponse(
            access_token=create_access_token(subject=subject),
            refresh_token=create_refresh_token(subject=subject),
        )
