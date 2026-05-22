import pytest
import uuid
from datetime import datetime, date, timezone
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient
from app.core.dependencies import get_db
from app.main import app
from app.models.invoice import Invoice, InvoiceStatus
from app.models.invoice_item import InvoiceItem

# Sample UUIDs for testing
mock_business_id = uuid.uuid4()
mock_customer_id = uuid.uuid4()
mock_user_id = uuid.uuid4()
mock_invoice_id = uuid.uuid4()

# Helper to build mock invoice
def get_mock_invoice(status: InvoiceStatus = InvoiceStatus.DRAFT) -> Invoice:
    item_id = uuid.uuid4()
    item = InvoiceItem(
        id=item_id,
        invoice_id=mock_invoice_id,
        product_name="Consulting Services",
        quantity=2.0000,
        unit_price=100.00,
        vat_rate=13.00,
        discount=10.00,
        line_total=190.00
    )
    invoice = Invoice(
        id=mock_invoice_id,
        business_id=mock_business_id,
        customer_id=mock_customer_id,
        invoice_number="INV-2026-0001",
        status=status,
        subtotal=190.00,
        vat_amount=24.70,
        discount_amount=5.00,
        total_amount=209.70,
        due_date=date(2026, 6, 1),
        notes="Thank you for your business!",
        created_by=mock_user_id,
        created_at=datetime.now(timezone.utc),
        items=[item]
    )
    item.invoice = invoice
    return invoice


@pytest.mark.anyio
async def test_get_invoice_not_found(client: AsyncClient):
    db_mock = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = None
    db_mock.execute.return_value = result_mock

    app.dependency_overrides[get_db] = lambda: db_mock

    try:
        response = await client.get(f"/api/v1/invoices/{uuid.uuid4()}")
        assert response.status_code == 404
        assert response.json()["error"].endswith("not found")
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_get_invoice_success(client: AsyncClient):
    db_mock = AsyncMock()
    result_mock = MagicMock()
    mock_invoice = get_mock_invoice()
    result_mock.scalars.return_value.first.return_value = mock_invoice
    db_mock.execute.return_value = result_mock

    app.dependency_overrides[get_db] = lambda: db_mock

    try:
        response = await client.get(f"/api/v1/invoices/{mock_invoice_id}")
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["id"] == str(mock_invoice_id)
        assert data["invoice_number"] == "INV-2026-0001"
        assert len(data["items"]) == 1
        assert data["items"][0]["product_name"] == "Consulting Services"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_get_customer_invoices_success(client: AsyncClient):
    db_mock = AsyncMock()
    result_mock = MagicMock()
    mock_invoice = get_mock_invoice()
    result_mock.scalars.return_value.all.return_value = [mock_invoice]
    db_mock.execute.return_value = result_mock

    app.dependency_overrides[get_db] = lambda: db_mock

    try:
        response = await client.get(
            f"/api/v1/invoices/customer/{mock_customer_id}",
            params={"business_id": str(mock_business_id)},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert len(data) == 1
        assert data[0]["customer_id"] == str(mock_customer_id)
        assert data[0]["business_id"] == str(mock_business_id)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_create_invoice_success(client: AsyncClient):
    db_mock = AsyncMock()
    
    # 1st execute: checking uniqueness (get_by_invoice_number) -> None
    # 2nd execute: getting latest invoice number for auto generation -> None
    exec_result_1 = MagicMock()
    exec_result_1.scalars.return_value.first.return_value = None
    
    exec_result_2 = MagicMock()
    exec_result_2.scalars.return_value.first.return_value = None
    
    db_mock.execute.side_effect = [exec_result_1, exec_result_2]

    # Mock refresh to set generated id and timestamps
    async def mock_refresh(invoice):
        invoice.id = mock_invoice_id
        invoice.created_at = datetime.now(timezone.utc)
        for i, item in enumerate(invoice.items):
            item.id = uuid.uuid4()
            item.invoice_id = invoice.id

    db_mock.refresh = mock_refresh
    db_mock.add = MagicMock()

    app.dependency_overrides[get_db] = lambda: db_mock

    payload = {
        "business_id": str(mock_business_id),
        "customer_id": str(mock_customer_id),
        "discount_amount": 5.00,
        "due_date": "2026-06-01",
        "notes": "Thank you!",
        "created_by": str(mock_user_id),
        "items": [
            {
                "product_name": "Consulting Services",
                "quantity": 2,
                "unit_price": 100.00,
                "vat_rate": 13.00,
                "discount": 10.00
            }
        ]
    }

    try:
        response = await client.post("/api/v1/invoices/", json=payload)
        assert response.status_code == 201
        data = response.json()["result"]
        # Expected subtotal = 2 * 100 - 10 = 190.00
        # Expected vat_amount = 190 * 0.13 = 24.70
        # Expected total = 190 + 24.70 - 5.00 = 209.70
        assert data["subtotal"] == "190.00"
        assert data["vat_amount"] == "24.70"
        assert data["total_amount"] == "209.70"
        assert data["invoice_number"].startswith("INV-2026-")
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_update_draft_invoice_success(client: AsyncClient):
    db_mock = AsyncMock()
    mock_invoice = get_mock_invoice(InvoiceStatus.DRAFT)
    
    # Mock lookup
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = mock_invoice
    db_mock.execute.return_value = result_mock

    app.dependency_overrides[get_db] = lambda: db_mock

    payload = {
        "notes": "Updated note!",
        "discount_amount": 10.00
    }

    try:
        response = await client.put(f"/api/v1/invoices/{mock_invoice_id}", json=payload)
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["notes"] == "Updated note!"
        # New total should be subtotal(190) + vat(24.70) - new_discount(10) = 204.70
        assert data["total_amount"] == "204.70"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_update_finalized_invoice_fails(client: AsyncClient):
    db_mock = AsyncMock()
    mock_invoice = get_mock_invoice(InvoiceStatus.SENT)  # Finalized status
    
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = mock_invoice
    db_mock.execute.return_value = result_mock

    app.dependency_overrides[get_db] = lambda: db_mock

    payload = {
        "notes": "Try updating notes"
    }

    try:
        response = await client.put(f"/api/v1/invoices/{mock_invoice_id}", json=payload)
        assert response.status_code == 400
        assert "Only draft invoices can be modified" in response.json()["error"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_finalize_invoice_success(client: AsyncClient):
    db_mock = AsyncMock()
    mock_invoice = get_mock_invoice(InvoiceStatus.DRAFT)
    
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = mock_invoice
    db_mock.execute.return_value = result_mock

    app.dependency_overrides[get_db] = lambda: db_mock

    try:
        response = await client.post(f"/api/v1/invoices/{mock_invoice_id}/finalize")
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["status"] == "Sent"
    finally:
        app.dependency_overrides.clear()
