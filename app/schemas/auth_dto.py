from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class LoginRequest(BaseModel):
    """Payload expected on POST /auth/login."""

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=100)


class TokenResponse(BaseModel):
    """Token payload returned after a successful login."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded claims extracted from a verified JWT — used internally."""

    sub: str
    type: str
