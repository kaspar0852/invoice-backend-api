import re
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from app.schemas.user import UserRead


class LoginRequest(BaseModel):
    """Payload expected on POST /auth/login."""

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=100)


class TokenResponse(BaseModel):
    """Token payload returned after a successful login."""

    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded claims extracted from a verified JWT — used internally."""

    sub: str
    type: str


class RegisterRequest(BaseModel):
    """Payload expected on POST /auth/register."""

    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        value = value.strip()
        if not re.match(r"^[a-zA-Z\s'\-]+$", value):
            raise ValueError("Full name must contain only letters, spaces, hyphens, or apostrophes")
        return value

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        """Enforce a strong password policy before the value is accepted."""
        errors = []
        if not re.search(r"[A-Z]", value):
            errors.append("one uppercase letter")
        if not re.search(r"[a-z]", value):
            errors.append("one lowercase letter")
        if not re.search(r"\d", value):
            errors.append("one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+\[\]\\/]", value):
            errors.append("one special character")
        if errors:
            raise ValueError(f"Password must contain at least: {', '.join(errors)}")
        return value

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class RegisterResponse(TokenResponse):
    """Returned after successful registration — tokens plus the new user profile."""

    user: UserRead
