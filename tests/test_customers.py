import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient
from app.core.dependencies import get_db
from app.main import app
from app.models import Customer

# Sample customer model instance
mock_customer_id = uuid.uuid4()
mock_business_id = uuid.uuid4()
mock_customer = Customer(
    id=mock_customer_id,
    business_id=mock_business_id,
    name="John Doe",
    phone="1234567890",
    email="john@example.com",
    address="123 Main St",
    vat_number="VAT123",
    created_at=datetime.now(timezone.utc),
)


@pytest.mark.anyio
async def test_get_customer_not_found(client: AsyncClient):
    db_mock = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = None
    db_mock.execute.return_value = result_mock

    app.dependency_overrides[get_db] = lambda: db_mock

    try:
        response = await client.get(
            f"/api/v1/customers/{uuid.uuid4()}",
            params={"business_id": str(mock_business_id)},
        )
        assert response.status_code == 404
        assert response.json()["error"].endswith("not found")
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_get_customer_success(client: AsyncClient):
    db_mock = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = mock_customer
    db_mock.execute.return_value = result_mock

    app.dependency_overrides[get_db] = lambda: db_mock

    try:
        response = await client.get(
            f"/api/v1/customers/{mock_customer_id}",
            params={"business_id": str(mock_business_id)},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["email"] == "john@example.com"
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["id"] == str(mock_customer_id)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_create_customer_success(client: AsyncClient):
    db_mock = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = None
    db_mock.execute.return_value = result_mock

    async def mock_refresh(customer):
        customer.id = mock_customer_id
        customer.created_at = datetime.now(timezone.utc)
    db_mock.refresh = mock_refresh
    db_mock.add = MagicMock()

    app.dependency_overrides[get_db] = lambda: db_mock

    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone_number": "+1234567890",
        "address": "123 Main St",
        "vat_number": "VAT123",
        "business_id": str(mock_business_id),
    }

    try:
        response = await client.post("/api/v1/customers/", json=payload)
        assert response.status_code == 201
        data = response.json()["result"]
        assert data["email"] == "john.doe@example.com"
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert "id" in data
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_create_customer_invalid_email(client: AsyncClient):
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "invalid-email-address",
        "phone_number": "+1234567890",
        "address": "123 Main St",
        "vat_number": "VAT123",
        "business_id": str(mock_business_id),
    }

    response = await client.post("/api/v1/customers/", json=payload)
    assert response.status_code == 422
    assert response.json()["success"] is False
    assert "error" in response.json()
