from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from fastapi import HTTPException, status

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

# Single shared PasswordHash instance using bcrypt as the hashing backend.
# This is intentionally module-level so the hasher is constructed once.
_password_hasher = PasswordHash((BcryptHasher(),))


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt (via pwdlib).

    Returns a self-contained hash string that embeds the salt and algorithm
    identifier, safe to store directly in the database.
    """
    return _password_hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a stored bcrypt hash.

    Returns True if the password matches, False otherwise.
    Never raises on a bad password — only raises if the hash itself is
    structurally invalid (handled upstream by the service layer).
    """
    return _password_hasher.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT token handling
# ---------------------------------------------------------------------------

def create_access_token(subject: str, extra_claims: Optional[dict] = None) -> str:
    """Create a signed JWT access token.

    :param subject: Unique identifier embedded in `sub` (typically the user UUID).
    :param extra_claims: Optional dict of additional claims merged into the payload.
    :returns: Encoded JWT string ready to return to the client.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict = {
        "sub": subject,
        "exp": expire,
        "iat": now,
        "type": "access",
    }

    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """Create a signed JWT refresh token with a longer expiry window.

    :param subject: Unique identifier embedded in `sub` (typically the user UUID).
    :returns: Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload: dict = {
        "sub": subject,
        "exp": expire,
        "iat": now,
        "type": "refresh",
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and cryptographically verify a JWT token.

    Validates the signature, expiry, and structure in one step.
    Raises HTTP 401 for any failure so callers never see raw JWTError.

    :param token: Raw JWT string from the Authorization header.
    :returns: Decoded payload dict (contains 'sub', 'type', 'exp', etc.).
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
