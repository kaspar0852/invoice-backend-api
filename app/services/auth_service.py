from fastapi import HTTPException, status

from app.models.user import User
from app.repositories.user import UserRepositoryInterface
from app.schemas.auth_dto import LoginRequest, TokenResponse, RegisterRequest, RegisterResponse
from app.schemas.user import UserRead
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token


class AuthService:
    def __init__(self, repository: UserRepositoryInterface):
        self.repository = repository

    async def register(self, data: RegisterRequest) -> RegisterResponse:
        """Register a new user account and return tokens immediately (auto-login).

        Checks email uniqueness first, then creates the user with a hashed
        password and issues access + refresh tokens so the client is logged
        in without a separate login call.
        """
        existing = await self.repository.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        new_user = User(
            email=data.email,
            full_name=data.full_name,
            phone=data.phone,
            is_active=True,
            password_hash=hash_password(data.password),  # plain text never persisted
        )

        created = await self.repository.create(new_user)
        subject = str(created.id)

        return RegisterResponse(
            access_token=create_access_token(subject=subject),
            refresh_token=create_refresh_token(subject=subject),
            user=UserRead.model_validate(created),
        )
        

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
