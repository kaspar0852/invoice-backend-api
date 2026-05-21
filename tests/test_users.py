import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient
from app.core.dependencies import get_db
from app.main import app
from app.models.user import User

# Sample user model instance
mock_user_id = uuid.uuid4()
mock_user = User(
    id=mock_user_id,
    email="test@example.com",
    full_name="Test User",
    phone=None,
    password_hash="hashed_password",
    is_active=True,
    created_at=datetime.now(timezone.utc),
)


@pytest.mark.anyio
async def test_get_user_not_found(client: AsyncClient):
    db_mock = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = None
    db_mock.execute.return_value = result_mock

    # Override get_db dependency
    app.dependency_overrides[get_db] = lambda: db_mock

    try:
        response = await client.get(f"/api/v1/users/{uuid.uuid4()}")
        assert response.status_code == 404
        assert response.json()["detail"].endswith("not found")
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_get_user_success(client: AsyncClient):
    db_mock = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = mock_user
    db_mock.execute.return_value = result_mock

    app.dependency_overrides[get_db] = lambda: db_mock

    try:
        response = await client.get(f"/api/v1/users/{mock_user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["id"] == str(mock_user_id)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_create_user_success(client: AsyncClient):
    db_mock = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = None
    db_mock.execute.return_value = result_mock

    # Mock refresh to populate database-generated fields
    async def mock_refresh(user):
        user.id = uuid.uuid4()
        user.created_at = datetime.now(timezone.utc)
    db_mock.refresh = mock_refresh
    db_mock.add = MagicMock()

    app.dependency_overrides[get_db] = lambda: db_mock

    payload = {
        "email": "newuser@example.com",
        "full_name": "New User",
        "password": "supersecretpassword"
    }

    try:
        response = await client.post("/api/v1/users/", json=payload)
        # Because create actually executes commit & refresh on the returned object,
        # and we mocked the session, we should get a valid JSON response matching UserRead
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
    finally:
        app.dependency_overrides.clear()
