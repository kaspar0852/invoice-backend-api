from datetime import date, datetime, timezone
from decimal import Decimal
import uuid
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.dependencies import get_db
from app.main import app
from app.models.business import Business
from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard_dto import (
    FinancialSummaryResponse,
    MetricsSummary,
    OutstandingPaymentsResponse,
    OutstandingStatusFilter,
    OutstandingSummary,
)
from app.services.dashboard_service import DashboardService


FIXED_TODAY = date(2026, 5, 23)


@pytest.fixture
async def dashboard_db_session() -> AsyncSession:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def dashboard_fixture_data(dashboard_db_session: AsyncSession) -> dict[str, uuid.UUID]:
    business_a_id = uuid.uuid4()
    business_b_id = uuid.uuid4()
    customer_a_id = uuid.uuid4()
    customer_a2_id = uuid.uuid4()
    customer_b_id = uuid.uuid4()

    dashboard_db_session.add_all(
        [
            Business(id=business_a_id, name="Business A"),
            Business(id=business_b_id, name="Business B"),
            Customer(
                id=customer_a_id,
                business_id=business_a_id,
                name="Alice Example",
                email="alice@example.com",
                phone="+15550000001",
                created_at=datetime.now(timezone.utc),
            ),
            Customer(
                id=customer_a2_id,
                business_id=business_a_id,
                name="Ava Example",
                email="ava@example.com",
                phone="+15550000003",
                created_at=datetime.now(timezone.utc),
            ),
            Customer(
                id=customer_b_id,
                business_id=business_b_id,
                name="Bob Example",
                email="bob@example.com",
                phone="+15550000002",
                created_at=datetime.now(timezone.utc),
            ),
        ]
    )

    invoices = [
        Invoice(
            id=uuid.uuid4(),
            business_id=business_a_id,
            customer_id=customer_a_id,
            invoice_number="A-SENT-001",
            status=InvoiceStatus.SENT,
            subtotal=Decimal("1000.00"),
            vat_amount=Decimal("130.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("1000.00"),
            due_date=date(2026, 5, 10),
        ),
        Invoice(
            id=uuid.uuid4(),
            business_id=business_a_id,
            customer_id=customer_a_id,
            invoice_number="A-PARTIAL-001",
            status=InvoiceStatus.PARTIAL,
            subtotal=Decimal("800.00"),
            vat_amount=Decimal("200.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("1000.00"),
            due_date=date(2026, 5, 30),
        ),
        Invoice(
            id=uuid.uuid4(),
            business_id=business_a_id,
            customer_id=customer_a_id,
            invoice_number="A-OVERDUE-001",
            status=InvoiceStatus.OVERDUE,
            subtotal=Decimal("348.00"),
            vat_amount=Decimal("52.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("400.00"),
            due_date=date(2026, 5, 1),
        ),
        Invoice(
            id=uuid.uuid4(),
            business_id=business_a_id,
            customer_id=customer_a_id,
            invoice_number="A-PAID-001",
            status=InvoiceStatus.PAID,
            subtotal=Decimal("696.00"),
            vat_amount=Decimal("104.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("800.00"),
            due_date=date(2026, 5, 5),
        ),
        Invoice(
            id=uuid.uuid4(),
            business_id=business_a_id,
            customer_id=customer_a_id,
            invoice_number="A-DRAFT-001",
            status=InvoiceStatus.DRAFT,
            subtotal=Decimal("174.00"),
            vat_amount=Decimal("26.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("200.00"),
            due_date=date(2026, 5, 15),
        ),
        Invoice(
            id=uuid.uuid4(),
            business_id=business_a_id,
            customer_id=customer_a_id,
            invoice_number="A-CANCELLED-001",
            status=InvoiceStatus.CANCELLED,
            subtotal=Decimal("130.50"),
            vat_amount=Decimal("19.50"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("150.00"),
            due_date=date(2026, 5, 6),
        ),
        Invoice(
            id=uuid.uuid4(),
            business_id=business_a_id,
            customer_id=customer_a_id,
            invoice_number="A-ZERO-001",
            status=InvoiceStatus.PAID,
            subtotal=Decimal("0.00"),
            vat_amount=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("0.00"),
            due_date=None,
        ),
        Invoice(
            id=uuid.uuid4(),
            business_id=business_a_id,
            customer_id=customer_a2_id,
            invoice_number="A-SENT-NULL-001",
            status=InvoiceStatus.SENT,
            subtotal=Decimal("261.00"),
            vat_amount=Decimal("39.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("300.00"),
            due_date=None,
        ),
        Invoice(
            id=uuid.uuid4(),
            business_id=business_b_id,
            customer_id=customer_b_id,
            invoice_number="B-OVERDUE-001",
            status=InvoiceStatus.OVERDUE,
            subtotal=Decimal("630.00"),
            vat_amount=Decimal("70.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("700.00"),
            due_date=date(2026, 5, 8),
        ),
    ]
    dashboard_db_session.add_all(invoices)

    payments = [
        Payment(
            id=uuid.uuid4(),
            invoice_id=invoices[1].id,
            business_id=business_a_id,
            amount=Decimal("500.00"),
            payment_date=date(2026, 5, 20),
            payment_method=PaymentMethod.BANK,
            status=PaymentStatus.SETTLED,
        ),
        Payment(
            id=uuid.uuid4(),
            invoice_id=invoices[3].id,
            business_id=business_a_id,
            amount=Decimal("800.00"),
            payment_date=date(2026, 5, 10),
            payment_method=PaymentMethod.BANK,
            status=PaymentStatus.SETTLED,
        ),
        Payment(
            id=uuid.uuid4(),
            invoice_id=invoices[2].id,
            business_id=business_a_id,
            amount=Decimal("250.00"),
            payment_date=date(2026, 4, 30),
            payment_method=PaymentMethod.CASH,
            status=PaymentStatus.SETTLED,
        ),
        Payment(
            id=uuid.uuid4(),
            invoice_id=invoices[0].id,
            business_id=business_a_id,
            amount=Decimal("300.00"),
            payment_date=date(2026, 5, 12),
            payment_method=PaymentMethod.CASH,
            status=PaymentStatus.PENDING,
        ),
        Payment(
            id=uuid.uuid4(),
            invoice_id=invoices[1].id,
            business_id=business_a_id,
            amount=Decimal("50.00"),
            payment_date=date(2026, 5, 21),
            payment_method=PaymentMethod.MOBILE,
            status=PaymentStatus.FAILED,
        ),
        Payment(
            id=uuid.uuid4(),
            invoice_id=invoices[0].id,
            business_id=business_a_id,
            amount=Decimal("25.00"),
            payment_date=date(2026, 5, 22),
            payment_method=PaymentMethod.CHEQUE,
            status=PaymentStatus.REFUNDED,
        ),
        Payment(
            id=uuid.uuid4(),
            invoice_id=invoices[6].id,
            business_id=business_a_id,
            amount=Decimal("100.00"),
            payment_date=date(2026, 5, 18),
            payment_method=PaymentMethod.BANK,
            status=PaymentStatus.SETTLED,
        ),
        Payment(
            id=uuid.uuid4(),
            invoice_id=invoices[8].id,
            business_id=business_b_id,
            amount=Decimal("200.00"),
            payment_date=date(2026, 5, 14),
            payment_method=PaymentMethod.BANK,
            status=PaymentStatus.SETTLED,
        ),
    ]
    dashboard_db_session.add_all(payments)
    await dashboard_db_session.commit()

    return {
        "business_a_id": business_a_id,
        "business_b_id": business_b_id,
        "customer_a_id": customer_a_id,
        "customer_a2_id": customer_a2_id,
        "customer_b_id": customer_b_id,
        "invoice_sent_id": invoices[0].id,
        "invoice_partial_id": invoices[1].id,
        "invoice_overdue_id": invoices[2].id,
        "invoice_null_due_id": invoices[7].id,
    }


def build_service(repository) -> DashboardService:
    service = DashboardService(repository)
    service._today = lambda: FIXED_TODAY
    return service


@pytest.mark.anyio
async def test_dashboard_dto_rounds_and_serializes() -> None:
    metrics = MetricsSummary(
        revenue=Decimal("100.005"),
        vat_liability=Decimal("20.335"),
        outstanding_receivables=Decimal("50"),
    )

    assert metrics.revenue == Decimal("100.01")
    assert metrics.vat_liability == Decimal("20.34")
    assert metrics.outstanding_receivables == Decimal("50.00")
    assert metrics.model_dump(mode="json") == {
        "revenue": 100.01,
        "vat_liability": 20.34,
        "outstanding_receivables": 50.0,
    }

    summary = OutstandingSummary(
        total_outstanding=Decimal("1950.005"),
        total_invoices=4,
    )
    assert summary.model_dump(mode="json") == {
        "total_outstanding": 1950.01,
        "total_invoices": 4,
    }


@pytest.mark.anyio
async def test_dashboard_repository_revenue_queries(dashboard_db_session: AsyncSession, dashboard_fixture_data: dict[str, uuid.UUID]) -> None:
    repository = DashboardRepository(dashboard_db_session)

    revenue = await repository.get_revenue(
        dashboard_fixture_data["business_a_id"],
        date(2026, 5, 1),
        date(2026, 5, 31),
    )
    empty_revenue = await repository.get_revenue(
        dashboard_fixture_data["business_a_id"],
        date(2026, 3, 1),
        date(2026, 3, 31),
    )
    other_business_revenue = await repository.get_revenue(
        dashboard_fixture_data["business_b_id"],
        date(2026, 5, 1),
        date(2026, 5, 31),
    )

    assert revenue == Decimal("1400.00")
    assert empty_revenue == Decimal("0.00")
    assert other_business_revenue == Decimal("200.00")


@pytest.mark.anyio
async def test_dashboard_repository_vat_liability_queries(dashboard_db_session: AsyncSession, dashboard_fixture_data: dict[str, uuid.UUID]) -> None:
    repository = DashboardRepository(dashboard_db_session)

    vat_liability = await repository.get_vat_liability(
        dashboard_fixture_data["business_a_id"],
        date(2026, 5, 1),
        date(2026, 5, 31),
    )
    empty_vat = await repository.get_vat_liability(
        dashboard_fixture_data["business_a_id"],
        date(2026, 3, 1),
        date(2026, 3, 31),
    )

    assert vat_liability == Decimal("204.00")
    assert empty_vat == Decimal("0.00")


@pytest.mark.anyio
async def test_dashboard_repository_outstanding_receivables_queries(dashboard_db_session: AsyncSession, dashboard_fixture_data: dict[str, uuid.UUID]) -> None:
    repository = DashboardRepository(dashboard_db_session)

    receivables = await repository.get_outstanding_receivables(dashboard_fixture_data["business_a_id"])
    other_business_receivables = await repository.get_outstanding_receivables(dashboard_fixture_data["business_b_id"])

    assert receivables == Decimal("1950.00")
    assert other_business_receivables == Decimal("500.00")


@pytest.mark.anyio
async def test_dashboard_repository_outstanding_invoices_query(
    dashboard_db_session: AsyncSession,
    dashboard_fixture_data: dict[str, uuid.UUID],
) -> None:
    repository = DashboardRepository(dashboard_db_session)

    rows = await repository.get_outstanding_invoices(
        business_id=dashboard_fixture_data["business_a_id"],
        limit=10,
        offset=0,
    )

    assert [row.invoice_number for row in rows] == [
        "A-OVERDUE-001",
        "A-SENT-001",
        "A-PARTIAL-001",
        "A-SENT-NULL-001",
    ]
    assert rows[0].aging_days == 22
    assert rows[1].aging_days == 13
    assert rows[2].aging_days == -7
    assert rows[3].aging_days is None
    assert rows[0].remaining_balance == Decimal("150.00")
    assert rows[1].remaining_balance == Decimal("1000.00")
    assert rows[2].remaining_balance == Decimal("500.00")
    assert rows[3].remaining_balance == Decimal("300.00")
    assert rows[3].customer_name == "Ava Example"
    assert rows[3].customer_email == "ava@example.com"
    assert rows[3].customer_phone == "+15550000003"


@pytest.mark.anyio
async def test_dashboard_repository_outstanding_invoice_filters_and_pagination(
    dashboard_db_session: AsyncSession,
    dashboard_fixture_data: dict[str, uuid.UUID],
) -> None:
    repository = DashboardRepository(dashboard_db_session)

    overdue_rows = await repository.get_outstanding_invoices(
        business_id=dashboard_fixture_data["business_a_id"],
        status=OutstandingStatusFilter.OVERDUE,
        limit=10,
        offset=0,
    )
    customer_rows = await repository.get_outstanding_invoices(
        business_id=dashboard_fixture_data["business_a_id"],
        customer_id=dashboard_fixture_data["customer_a2_id"],
        limit=10,
        offset=0,
    )
    paged_rows = await repository.get_outstanding_invoices(
        business_id=dashboard_fixture_data["business_a_id"],
        limit=2,
        offset=1,
    )
    other_business_rows = await repository.get_outstanding_invoices(
        business_id=dashboard_fixture_data["business_b_id"],
        limit=10,
        offset=0,
    )

    assert [row.invoice_number for row in overdue_rows] == ["A-OVERDUE-001"]
    assert [row.invoice_number for row in customer_rows] == ["A-SENT-NULL-001"]
    assert [row.invoice_number for row in paged_rows] == ["A-SENT-001", "A-PARTIAL-001"]
    assert [row.invoice_number for row in other_business_rows] == ["B-OVERDUE-001"]


@pytest.mark.anyio
async def test_dashboard_repository_outstanding_totals_query(
    dashboard_db_session: AsyncSession,
    dashboard_fixture_data: dict[str, uuid.UUID],
) -> None:
    repository = DashboardRepository(dashboard_db_session)

    total_outstanding, total_invoices = await repository.get_outstanding_totals(
        business_id=dashboard_fixture_data["business_a_id"],
    )
    overdue_total, overdue_count = await repository.get_outstanding_totals(
        business_id=dashboard_fixture_data["business_a_id"],
        status=OutstandingStatusFilter.OVERDUE,
    )
    customer_total, customer_count = await repository.get_outstanding_totals(
        business_id=dashboard_fixture_data["business_a_id"],
        customer_id=dashboard_fixture_data["customer_a2_id"],
    )
    empty_total, empty_count = await repository.get_outstanding_totals(
        business_id=dashboard_fixture_data["business_a_id"],
        customer_id=uuid.uuid4(),
    )

    assert total_outstanding == Decimal("1950.00")
    assert total_invoices == 4
    assert overdue_total == Decimal("150.00")
    assert overdue_count == 1
    assert customer_total == Decimal("300.00")
    assert customer_count == 1
    assert empty_total == Decimal("0.00")
    assert empty_count == 0


@pytest.mark.anyio
async def test_dashboard_service_applies_defaults_and_builds_response() -> None:
    repository = AsyncMock()
    repository.business_exists.return_value = True
    repository.get_revenue.return_value = Decimal("1400.00")
    repository.get_vat_liability.return_value = Decimal("204.00")
    repository.get_outstanding_receivables.return_value = Decimal("1950.00")

    business_id = uuid.uuid4()
    service = build_service(repository)
    response = await service.get_financial_summary(business_id=business_id, user_id=None)

    assert isinstance(response, FinancialSummaryResponse)
    assert response.business_id == business_id
    assert response.period.start_date == date(2026, 5, 1)
    assert response.period.end_date == FIXED_TODAY
    assert response.period.label == "May 2026 (month-to-date)"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("start_date", "end_date", "expected_message"),
    [
        ("2026-05-23", "2026-05-22", "end_date must be greater than or equal to start_date"),
        ("2026-05-01", "2026-05-24", "end_date cannot be in the future"),
        ("2025-05-22", "2026-05-23", "Date range cannot exceed 1 year (365 days)"),
    ],
)
async def test_dashboard_service_validation_errors(start_date: str, end_date: str, expected_message: str) -> None:
    repository = AsyncMock()
    repository.business_exists.return_value = True
    service = build_service(repository)

    with pytest.raises(Exception) as exc_info:
        await service.get_financial_summary(
            business_id=uuid.uuid4(),
            user_id=None,
            start_date=start_date,
            end_date=end_date,
        )

    exc = exc_info.value
    assert getattr(exc, "status_code", None) == 422
    assert getattr(exc, "detail", None) == expected_message


def test_dashboard_service_period_labels() -> None:
    repository = AsyncMock()
    service = build_service(repository)

    assert service._generate_period_label(date(2026, 5, 1), FIXED_TODAY) == "May 2026 (month-to-date)"
    assert service._generate_period_label(date(2026, 4, 1), date(2026, 4, 30)) == "April 2026"
    assert service._generate_period_label(date(2026, 5, 15), date(2026, 5, 22)) == "May 15 – May 22, 2026"


@pytest.mark.anyio
async def test_dashboard_route_happy_path_and_optional_params(
    client,
    dashboard_db_session: AsyncSession,
    dashboard_fixture_data: dict[str, uuid.UUID],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def override_get_db():
        yield dashboard_db_session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(DashboardService, "_today", lambda self: FIXED_TODAY)

    try:
        response = await client.get(
            "/api/v1/dashboard/financial-summary",
            params={"business_id": str(dashboard_fixture_data["business_a_id"])},
        )
        assert response.status_code == 200
        body = response.json()["result"]
        assert body["period"] == {
            "start_date": "2026-05-01",
            "end_date": "2026-05-23",
            "label": "May 2026 (month-to-date)",
        }
        assert body["metrics"] == {
            "revenue": 1400.0,
            "vat_liability": 204.0,
            "outstanding_receivables": 1950.0,
        }

        only_start = await client.get(
            "/api/v1/dashboard/financial-summary",
            params={
                "business_id": str(dashboard_fixture_data["business_a_id"]),
                "start_date": "2026-05-10",
            },
        )
        assert only_start.status_code == 200
        assert only_start.json()["result"]["period"]["label"] == "May 10 – May 23, 2026"

        explicit_range = await client.get(
            "/api/v1/dashboard/financial-summary",
            params={
                "business_id": str(dashboard_fixture_data["business_a_id"]),
                "start_date": "2026-05-01",
                "end_date": "2026-05-22",
            },
        )
        assert explicit_range.status_code == 200
        assert explicit_range.json()["result"]["period"]["label"] == "May 1 – May 22, 2026"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("params", "status_code", "message"),
    [
        (
            {"start_date": "2026-05-23", "end_date": "2026-05-22"},
            422,
            "end_date must be greater than or equal to start_date",
        ),
        (
            {"start_date": "2025-05-22", "end_date": "2026-05-23"},
            422,
            "Date range cannot exceed 1 year (365 days)",
        ),
        (
            {"start_date": "2026/05/01"},
            400,
            "Invalid date format. Use YYYY-MM-DD",
        ),
        (
            {"start_date": "2026-05-01", "end_date": "2026-05-24"},
            422,
            "end_date cannot be in the future",
        ),
    ],
)
async def test_dashboard_route_error_responses(
    client,
    dashboard_db_session: AsyncSession,
    dashboard_fixture_data: dict[str, uuid.UUID],
    monkeypatch: pytest.MonkeyPatch,
    params: dict[str, str],
    status_code: int,
    message: str,
) -> None:
    async def override_get_db():
        yield dashboard_db_session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(DashboardService, "_today", lambda self: FIXED_TODAY)

    try:
        response = await client.get(
            "/api/v1/dashboard/financial-summary",
            params={"business_id": str(dashboard_fixture_data["business_a_id"]), **params},
        )
        assert response.status_code == status_code
        assert response.json()["error"] == message
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_dashboard_route_unknown_business_returns_404(
    client,
    dashboard_db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def override_get_db():
        yield dashboard_db_session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(DashboardService, "_today", lambda self: FIXED_TODAY)

    try:
        response = await client.get(
            "/api/v1/dashboard/financial-summary",
            params={"business_id": str(uuid.uuid4())},
        )
        assert response.status_code == 404
        assert response.json()["error"] == "Business not found"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_dashboard_service_outstanding_payments_defaults_and_filters() -> None:
    repository = AsyncMock()
    repository.business_exists.return_value = True
    repository.get_outstanding_invoices.return_value = []
    repository.get_outstanding_totals.return_value = (Decimal("0.00"), 0)

    business_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    service = build_service(repository)
    response = await service.get_outstanding_payments(
        business_id=business_id,
        user_id=None,
        status_filter=OutstandingStatusFilter.OVERDUE,
        customer_id=customer_id,
        limit=250,
        offset=None,
    )

    assert isinstance(response, OutstandingPaymentsResponse)
    repository.get_outstanding_invoices.assert_awaited_once_with(
        business_id=business_id,
        status=OutstandingStatusFilter.OVERDUE,
        customer_id=customer_id,
        limit=200,
        offset=0,
    )
    repository.get_outstanding_totals.assert_awaited_once_with(
        business_id=business_id,
        status=OutstandingStatusFilter.OVERDUE,
        customer_id=customer_id,
    )
    assert response.pagination.limit == 200
    assert response.pagination.offset == 0
    assert response.pagination.total == 0


@pytest.mark.anyio
async def test_dashboard_service_outstanding_payments_business_not_found() -> None:
    repository = AsyncMock()
    repository.business_exists.return_value = False
    service = build_service(repository)

    with pytest.raises(Exception) as exc_info:
        await service.get_outstanding_payments(
            business_id=uuid.uuid4(),
            user_id=None,
        )

    exc = exc_info.value
    assert getattr(exc, "status_code", None) == 404
    assert getattr(exc, "detail", None) == "Business not found"


@pytest.mark.anyio
async def test_dashboard_route_outstanding_payments_happy_path(
    client,
    dashboard_db_session: AsyncSession,
    dashboard_fixture_data: dict[str, uuid.UUID],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def override_get_db():
        yield dashboard_db_session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(DashboardService, "_today", lambda self: FIXED_TODAY)

    try:
        response = await client.get(
            "/api/v1/dashboard/outstanding-payments",
            params={"business_id": str(dashboard_fixture_data["business_a_id"])},
        )
        assert response.status_code == 200
        body = response.json()["result"]
        assert body["summary"] == {
            "total_outstanding": 1950.0,
            "total_invoices": 4,
        }
        assert body["pagination"] == {
            "limit": 50,
            "offset": 0,
            "total": 4,
        }
        assert [row["status"] for row in body["invoices"]] == [
            "Overdue",
            "Sent",
            "Partial",
            "Sent",
        ]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_dashboard_route_outstanding_payments_filters_and_pagination(
    client,
    dashboard_db_session: AsyncSession,
    dashboard_fixture_data: dict[str, uuid.UUID],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def override_get_db():
        yield dashboard_db_session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(DashboardService, "_today", lambda self: FIXED_TODAY)

    try:
        overdue = await client.get(
            "/api/v1/dashboard/outstanding-payments",
            params={
                "business_id": str(dashboard_fixture_data["business_a_id"]),
                "status": "Overdue",
            },
        )
        assert overdue.status_code == 200
        overdue_body = overdue.json()["result"]
        assert [row["invoice_number"] for row in overdue_body["invoices"]] == ["A-OVERDUE-001"]
        assert overdue_body["pagination"]["total"] == 1

        customer_only = await client.get(
            "/api/v1/dashboard/outstanding-payments",
            params={
                "business_id": str(dashboard_fixture_data["business_a_id"]),
                "customer_id": str(dashboard_fixture_data["customer_a2_id"]),
            },
        )
        assert customer_only.status_code == 200
        assert [row["invoice_number"] for row in customer_only.json()["result"]["invoices"]] == ["A-SENT-NULL-001"]

        combined = await client.get(
            "/api/v1/dashboard/outstanding-payments",
            params={
                "business_id": str(dashboard_fixture_data["business_a_id"]),
                "status": "Sent",
                "customer_id": str(dashboard_fixture_data["customer_a2_id"]),
            },
        )
        assert combined.status_code == 200
        assert combined.json()["result"]["pagination"]["total"] == 1

        paged = await client.get(
            "/api/v1/dashboard/outstanding-payments",
            params={
                "business_id": str(dashboard_fixture_data["business_a_id"]),
                "limit": 2,
                "offset": 1,
            },
        )
        assert paged.status_code == 200
        paged_body = paged.json()["result"]
        assert [row["invoice_number"] for row in paged_body["invoices"]] == ["A-SENT-001", "A-PARTIAL-001"]
        assert paged_body["pagination"] == {
            "limit": 2,
            "offset": 1,
            "total": 4,
        }

        clamped = await client.get(
            "/api/v1/dashboard/outstanding-payments",
            params={
                "business_id": str(dashboard_fixture_data["business_a_id"]),
                "limit": 999,
            },
        )
        assert clamped.status_code == 200
        assert clamped.json()["result"]["pagination"]["limit"] == 200
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_dashboard_route_outstanding_payments_errors(
    client,
    dashboard_db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def override_get_db():
        yield dashboard_db_session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(DashboardService, "_today", lambda self: FIXED_TODAY)

    try:
        not_found = await client.get(
            "/api/v1/dashboard/outstanding-payments",
            params={"business_id": str(uuid.uuid4())},
        )
        assert not_found.status_code == 404
        assert not_found.json()["error"] == "Business not found"

        invalid_status = await client.get(
            "/api/v1/dashboard/outstanding-payments",
            params={
                "business_id": str(uuid.uuid4()),
                "status": "Draft",
            },
        )
        assert invalid_status.status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_dashboard_openapi_includes_financial_summary_route(client) -> None:
    response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/dashboard/financial-summary" in paths
    assert "/api/v1/dashboard/outstanding-payments" in paths
