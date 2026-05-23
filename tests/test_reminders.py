from datetime import date, datetime, timezone
from decimal import Decimal
from email.message import EmailMessage
from types import SimpleNamespace
import uuid
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_email_service
from app.core.database import Base
from app.core.dependencies import get_db
from app.main import app
from app.models.business import Business
from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.reminder_log import ReminderLog
from app.repositories.reminder_repository import ReminderInvoiceRecord, ReminderRepository
from app.schemas.reminder_dto import SendRemindersRequest, SendRemindersResponse
from app.services.email_service import EmailDeliveryError, EmailService
from app.services.reminder_service import ReminderService


FIXED_TODAY = date(2026, 5, 23)


class FakeEmailService:
    def __init__(self, failing_recipients: set[str] | None = None) -> None:
        self.failing_recipients = failing_recipients or set()
        self.sent_messages: list[dict[str, str]] = []

    def send(self, recipient_email: str, subject: str, body: str) -> None:
        if recipient_email in self.failing_recipients:
            raise EmailDeliveryError(f"SMTP failed for {recipient_email}")
        self.sent_messages.append(
            {
                "recipient_email": recipient_email,
                "subject": subject,
                "body": body,
            }
        )


@pytest.fixture
async def reminder_db_session() -> AsyncSession:
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
async def reminder_fixture_data(reminder_db_session: AsyncSession) -> dict[str, uuid.UUID]:
    business_a_id = uuid.uuid4()
    business_b_id = uuid.uuid4()
    customer_email_id = uuid.uuid4()
    customer_no_email_id = uuid.uuid4()
    customer_b_id = uuid.uuid4()

    reminder_db_session.add_all(
        [
            Business(id=business_a_id, name="Alpha Traders"),
            Business(id=business_b_id, name="Beta Traders"),
            Customer(
                id=customer_email_id,
                business_id=business_a_id,
                name="Alice Example",
                email="alice@example.com",
                phone="+15550000001",
                created_at=datetime.now(timezone.utc),
            ),
            Customer(
                id=customer_no_email_id,
                business_id=business_a_id,
                name="No Email Customer",
                email=None,
                phone="+15550000002",
                created_at=datetime.now(timezone.utc),
            ),
            Customer(
                id=customer_b_id,
                business_id=business_b_id,
                name="Bob Example",
                email="bob@example.com",
                phone="+15550000003",
                created_at=datetime.now(timezone.utc),
            ),
        ]
    )

    invoices = [
        Invoice(
            id=uuid.uuid4(),
            business_id=business_a_id,
            customer_id=customer_email_id,
            invoice_number="A-SENT-001",
            status=InvoiceStatus.SENT,
            subtotal=Decimal("800.00"),
            vat_amount=Decimal("100.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("900.00"),
            due_date=date(2026, 5, 20),
        ),
        Invoice(
            id=uuid.uuid4(),
            business_id=business_a_id,
            customer_id=customer_email_id,
            invoice_number="A-OVERDUE-001",
            status=InvoiceStatus.OVERDUE,
            subtotal=Decimal("600.00"),
            vat_amount=Decimal("100.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("700.00"),
            due_date=date(2026, 5, 10),
        ),
        Invoice(
            id=uuid.uuid4(),
            business_id=business_a_id,
            customer_id=customer_email_id,
            invoice_number="A-PAID-001",
            status=InvoiceStatus.PAID,
            subtotal=Decimal("400.00"),
            vat_amount=Decimal("100.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("500.00"),
            due_date=date(2026, 5, 15),
        ),
        Invoice(
            id=uuid.uuid4(),
            business_id=business_a_id,
            customer_id=customer_no_email_id,
            invoice_number="A-SENT-NOEMAIL-001",
            status=InvoiceStatus.SENT,
            subtotal=Decimal("300.00"),
            vat_amount=Decimal("50.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("350.00"),
            due_date=None,
        ),
        Invoice(
            id=uuid.uuid4(),
            business_id=business_a_id,
            customer_id=customer_email_id,
            invoice_number="A-PARTIAL-001",
            status=InvoiceStatus.PARTIAL,
            subtotal=Decimal("900.00"),
            vat_amount=Decimal("100.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("1000.00"),
            due_date=date(2026, 5, 28),
        ),
        Invoice(
            id=uuid.uuid4(),
            business_id=business_b_id,
            customer_id=customer_b_id,
            invoice_number="B-SENT-001",
            status=InvoiceStatus.SENT,
            subtotal=Decimal("450.00"),
            vat_amount=Decimal("50.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("500.00"),
            due_date=date(2026, 5, 22),
        ),
    ]
    reminder_db_session.add_all(invoices)

    payments = [
        Payment(
            id=uuid.uuid4(),
            invoice_id=invoices[0].id,
            business_id=business_a_id,
            amount=Decimal("300.00"),
            payment_date=date(2026, 5, 21),
            payment_method=PaymentMethod.BANK,
            status=PaymentStatus.SETTLED,
        ),
        Payment(
            id=uuid.uuid4(),
            invoice_id=invoices[0].id,
            business_id=business_a_id,
            amount=Decimal("50.00"),
            payment_date=date(2026, 5, 22),
            payment_method=PaymentMethod.CASH,
            status=PaymentStatus.PENDING,
        ),
        Payment(
            id=uuid.uuid4(),
            invoice_id=invoices[2].id,
            business_id=business_a_id,
            amount=Decimal("500.00"),
            payment_date=date(2026, 5, 18),
            payment_method=PaymentMethod.BANK,
            status=PaymentStatus.SETTLED,
        ),
        Payment(
            id=uuid.uuid4(),
            invoice_id=invoices[4].id,
            business_id=business_a_id,
            amount=Decimal("400.00"),
            payment_date=date(2026, 5, 20),
            payment_method=PaymentMethod.MOBILE,
            status=PaymentStatus.SETTLED,
        ),
        Payment(
            id=uuid.uuid4(),
            invoice_id=invoices[5].id,
            business_id=business_b_id,
            amount=Decimal("100.00"),
            payment_date=date(2026, 5, 22),
            payment_method=PaymentMethod.BANK,
            status=PaymentStatus.SETTLED,
        ),
    ]
    reminder_db_session.add_all(payments)
    await reminder_db_session.commit()

    return {
        "business_a_id": business_a_id,
        "business_b_id": business_b_id,
        "customer_email_id": customer_email_id,
        "customer_no_email_id": customer_no_email_id,
        "sent_invoice_id": invoices[0].id,
        "overdue_invoice_id": invoices[1].id,
        "paid_invoice_id": invoices[2].id,
        "no_email_invoice_id": invoices[3].id,
        "partial_invoice_id": invoices[4].id,
        "other_business_invoice_id": invoices[5].id,
    }


def build_record(
    *,
    invoice_id: uuid.UUID | None = None,
    business_id: uuid.UUID | None = None,
    business_name: str = "Alpha Traders",
    invoice_number: str = "INV-001",
    status: str = "Sent",
    total_amount: str = "900.00",
    remaining_balance: str = "600.00",
    due_date: date | None = date(2026, 5, 20),
    customer_id: uuid.UUID | None = None,
    customer_name: str = "Alice Example",
    customer_email: str | None = "alice@example.com",
    customer_phone: str | None = "+15550000001",
) -> ReminderInvoiceRecord:
    return ReminderInvoiceRecord(
        invoice_id=invoice_id or uuid.uuid4(),
        business_id=business_id or uuid.uuid4(),
        business_name=business_name,
        invoice_number=invoice_number,
        status=status,
        total_amount=Decimal(total_amount),
        remaining_balance=Decimal(remaining_balance),
        due_date=due_date,
        customer_id=customer_id or uuid.uuid4(),
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
    )


def build_service(repository, email_service) -> ReminderService:
    service = ReminderService(repository, email_service)
    service._today = lambda: FIXED_TODAY
    return service


def build_request(business_id: uuid.UUID, invoice_ids: list[uuid.UUID]) -> SendRemindersRequest:
    return SendRemindersRequest(business_id=business_id, invoice_ids=invoice_ids)


def build_email_stub_context():
    smtp_instance = MagicMock()
    smtp_context = MagicMock()
    smtp_context.__enter__.return_value = smtp_instance
    smtp_context.__exit__.return_value = False
    return smtp_context, smtp_instance


@pytest.mark.anyio
async def test_reminder_dtos_validate_and_serialize() -> None:
    payload = SendRemindersRequest(
        business_id=uuid.uuid4(),
        invoice_ids=[uuid.uuid4()],
    )
    response = SendRemindersResponse(
        sent=[
            {
                "invoice_id": uuid.uuid4(),
                "recipient_email": "alice@example.com",
                "customer_name": "Alice Example",
            }
        ],
        skipped=[
            {
                "invoice_id": uuid.uuid4(),
                "reason": "No email on file for this customer",
            }
        ],
    )

    assert len(payload.invoice_ids) == 1
    assert response.model_dump(mode="json")["sent"][0]["recipient_email"] == "alice@example.com"

    with pytest.raises(Exception):
        SendRemindersRequest(business_id=uuid.uuid4(), invoice_ids=[])


@pytest.mark.anyio
async def test_email_service_sends_plain_text_email() -> None:
    smtp_context, smtp_instance = build_email_stub_context()

    with patch("app.services.email_service.smtplib.SMTP", return_value=smtp_context):
        service = EmailService(
            host="smtp.gmail.com",
            port=587,
            username="sender@example.com",
            password="secret",
            from_name="Invoices Team",
        )
        service.send("alice@example.com", "Reminder", "Plain text body")

    smtp_instance.starttls.assert_called_once()
    smtp_instance.login.assert_called_once_with("sender@example.com", "secret")
    smtp_instance.send_message.assert_called_once()
    message: EmailMessage = smtp_instance.send_message.call_args.args[0]
    assert message["From"] == "Invoices Team <sender@example.com>"
    assert message["To"] == "alice@example.com"
    assert message["Subject"] == "Reminder"
    assert "Plain text body" in message.get_content()


@pytest.mark.anyio
async def test_email_service_wraps_smtp_errors() -> None:
    smtp_context, smtp_instance = build_email_stub_context()
    smtp_instance.send_message.side_effect = RuntimeError("smtp rejected recipient")

    with patch("app.services.email_service.smtplib.SMTP", return_value=smtp_context):
        service = EmailService(
            host="smtp.gmail.com",
            port=587,
            username="sender@example.com",
            password="secret",
            from_name="Invoices Team",
        )
        with pytest.raises(EmailDeliveryError) as exc_info:
            service.send("alice@example.com", "Reminder", "Body")

    assert "smtp rejected recipient" in str(exc_info.value)


@pytest.mark.anyio
async def test_reminder_repository_get_invoices_for_reminder(
    reminder_db_session: AsyncSession,
    reminder_fixture_data: dict[str, uuid.UUID],
) -> None:
    repository = ReminderRepository(reminder_db_session)
    rows = await repository.get_invoices_for_reminder(
        business_id=reminder_fixture_data["business_a_id"],
        invoice_ids=[
            reminder_fixture_data["sent_invoice_id"],
            reminder_fixture_data["other_business_invoice_id"],
            uuid.uuid4(),
        ],
    )

    assert len(rows) == 1
    assert rows[0].invoice_id == reminder_fixture_data["sent_invoice_id"]
    assert rows[0].customer_name == "Alice Example"
    assert rows[0].customer_email == "alice@example.com"
    assert rows[0].customer_phone == "+15550000001"
    assert rows[0].remaining_balance == Decimal("600.00")


@pytest.mark.anyio
async def test_reminder_repository_log_reminder_persists_rows(
    reminder_db_session: AsyncSession,
    reminder_fixture_data: dict[str, uuid.UUID],
) -> None:
    repository = ReminderRepository(reminder_db_session)

    await repository.log_reminder(
        invoice_id=reminder_fixture_data["sent_invoice_id"],
        business_id=reminder_fixture_data["business_a_id"],
        recipient_email="alice@example.com",
        channel="email",
        status="sent",
        error_message=None,
    )
    await repository.log_reminder(
        invoice_id=reminder_fixture_data["sent_invoice_id"],
        business_id=reminder_fixture_data["business_a_id"],
        recipient_email="alice@example.com",
        channel="email",
        status="failed",
        error_message="SMTP timeout",
    )

    logs = list(
        (
            await reminder_db_session.execute(
                select(ReminderLog).order_by(ReminderLog.sent_at.asc())
            )
        )
        .scalars()
        .all()
    )

    assert len(logs) == 2
    assert logs[0].status == "sent"
    assert logs[0].error_message is None
    assert logs[1].status == "failed"
    assert logs[1].error_message == "SMTP timeout"


@pytest.mark.anyio
async def test_reminder_service_sends_eligible_invoice_and_logs_success() -> None:
    business_id = uuid.uuid4()
    invoice_id = uuid.uuid4()
    repository = AsyncMock()
    repository.business_exists.return_value = True
    repository.get_invoices_for_reminder.return_value = [
        build_record(invoice_id=invoice_id, business_id=business_id, status="Sent")
    ]
    email_service = Mock()
    service = build_service(repository, email_service)

    response = await service.send_reminders(
        build_request(business_id, [invoice_id]),
        user_id=None,
    )

    assert response.sent[0].invoice_id == invoice_id
    email_service.send.assert_called_once()
    subject, body = email_service.send.call_args.args[1:]
    assert subject == "Payment reminder for invoice INV-001"
    assert "Alpha Traders" in body
    assert "Remaining balance: 600.00" in body
    repository.log_reminder.assert_awaited_once_with(
        invoice_id=invoice_id,
        business_id=business_id,
        recipient_email="alice@example.com",
        channel="email",
        status="sent",
        error_message=None,
    )


@pytest.mark.anyio
async def test_reminder_service_skips_missing_invoice_without_logging() -> None:
    business_id = uuid.uuid4()
    invoice_id = uuid.uuid4()
    repository = AsyncMock()
    repository.business_exists.return_value = True
    repository.get_invoices_for_reminder.return_value = []
    email_service = Mock()
    service = build_service(repository, email_service)

    response = await service.send_reminders(
        build_request(business_id, [invoice_id]),
        user_id=None,
    )

    assert response.sent == []
    assert response.skipped[0].reason == "Invoice not found or does not belong to this business"
    email_service.send.assert_not_called()
    repository.log_reminder.assert_not_awaited()


@pytest.mark.anyio
async def test_reminder_service_skips_non_outstanding_status() -> None:
    business_id = uuid.uuid4()
    invoice_id = uuid.uuid4()
    repository = AsyncMock()
    repository.business_exists.return_value = True
    repository.get_invoices_for_reminder.return_value = [
        build_record(invoice_id=invoice_id, business_id=business_id, status="Paid", remaining_balance="0.00")
    ]
    email_service = Mock()
    service = build_service(repository, email_service)

    response = await service.send_reminders(
        build_request(business_id, [invoice_id]),
        user_id=None,
    )

    assert response.skipped[0].reason == "Invoice status is not outstanding (status: Paid)"
    email_service.send.assert_not_called()
    repository.log_reminder.assert_not_awaited()


@pytest.mark.anyio
async def test_reminder_service_skips_missing_email() -> None:
    business_id = uuid.uuid4()
    invoice_id = uuid.uuid4()
    repository = AsyncMock()
    repository.business_exists.return_value = True
    repository.get_invoices_for_reminder.return_value = [
        build_record(invoice_id=invoice_id, business_id=business_id, customer_email=None)
    ]
    email_service = Mock()
    service = build_service(repository, email_service)

    response = await service.send_reminders(
        build_request(business_id, [invoice_id]),
        user_id=None,
    )

    assert response.skipped[0].reason == "No email on file for this customer"
    email_service.send.assert_not_called()
    repository.log_reminder.assert_not_awaited()


@pytest.mark.anyio
async def test_reminder_service_logs_smtp_failure_and_continues() -> None:
    business_id = uuid.uuid4()
    failing_invoice_id = uuid.uuid4()
    good_invoice_id = uuid.uuid4()
    repository = AsyncMock()
    repository.business_exists.return_value = True
    repository.get_invoices_for_reminder.return_value = [
        build_record(invoice_id=failing_invoice_id, business_id=business_id, customer_email="fail@example.com"),
        build_record(invoice_id=good_invoice_id, business_id=business_id, customer_email="ok@example.com"),
    ]
    email_service = FakeEmailService({"fail@example.com"})
    service = build_service(repository, email_service)

    response = await service.send_reminders(
        build_request(business_id, [failing_invoice_id, good_invoice_id]),
        user_id=None,
    )

    assert [item.invoice_id for item in response.sent] == [good_invoice_id]
    assert response.skipped[0].reason == "SMTP failed for fail@example.com"
    assert repository.log_reminder.await_count == 2
    first_call = repository.log_reminder.await_args_list[0].kwargs
    second_call = repository.log_reminder.await_args_list[1].kwargs
    assert first_call["status"] == "failed"
    assert first_call["error_message"] == "SMTP failed for fail@example.com"
    assert second_call["status"] == "sent"


@pytest.mark.anyio
async def test_reminder_service_renders_null_due_date_and_omits_aging_when_not_overdue() -> None:
    business_id = uuid.uuid4()
    invoice_id = uuid.uuid4()
    repository = AsyncMock()
    repository.business_exists.return_value = True
    repository.get_invoices_for_reminder.return_value = [
        build_record(
            invoice_id=invoice_id,
            business_id=business_id,
            due_date=None,
            status="Sent",
        )
    ]
    email_service = Mock()
    service = build_service(repository, email_service)

    await service.send_reminders(
        build_request(business_id, [invoice_id]),
        user_id=None,
    )

    body = email_service.send.call_args.args[2]
    assert "Due date: Not specified" in body
    assert "days overdue" not in body


@pytest.mark.anyio
async def test_reminder_service_unknown_business_returns_404() -> None:
    repository = AsyncMock()
    repository.business_exists.return_value = False
    email_service = Mock()
    service = build_service(repository, email_service)

    with pytest.raises(Exception) as exc_info:
        await service.send_reminders(
            build_request(uuid.uuid4(), [uuid.uuid4()]),
            user_id=None,
        )

    exc = exc_info.value
    assert getattr(exc, "status_code", None) == 404
    assert getattr(exc, "detail", None) == "Business not found"


@pytest.mark.anyio
async def test_reminder_route_all_sent(
    client,
    reminder_db_session: AsyncSession,
    reminder_fixture_data: dict[str, uuid.UUID],
) -> None:
    fake_email_service = FakeEmailService()

    async def override_get_db():
        yield reminder_db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_email_service] = lambda: fake_email_service

    try:
        response = await client.post(
            "/api/v1/dashboard/reminders",
            json={
                "business_id": str(reminder_fixture_data["business_a_id"]),
                "invoice_ids": [str(reminder_fixture_data["sent_invoice_id"])],
            },
        )
        assert response.status_code == 200
        body = response.json()["result"]
        SendRemindersResponse.model_validate(body)
        assert len(body["sent"]) == 1
        assert body["skipped"] == []

        logs = list((await reminder_db_session.execute(select(ReminderLog))).scalars().all())
        assert len(logs) == 1
        assert logs[0].status == "sent"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_reminder_route_all_skipped(
    client,
    reminder_db_session: AsyncSession,
    reminder_fixture_data: dict[str, uuid.UUID],
) -> None:
    fake_email_service = FakeEmailService()

    async def override_get_db():
        yield reminder_db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_email_service] = lambda: fake_email_service

    try:
        response = await client.post(
            "/api/v1/dashboard/reminders",
            json={
                "business_id": str(reminder_fixture_data["business_a_id"]),
                "invoice_ids": [
                    str(reminder_fixture_data["paid_invoice_id"]),
                    str(reminder_fixture_data["no_email_invoice_id"]),
                    str(uuid.uuid4()),
                ],
            },
        )
        assert response.status_code == 200
        body = response.json()["result"]
        assert body["sent"] == []
        assert [item["reason"] for item in body["skipped"]] == [
            "Invoice status is not outstanding (status: Paid)",
            "No email on file for this customer",
            "Invoice not found or does not belong to this business",
        ]
        assert fake_email_service.sent_messages == []
        logs = list((await reminder_db_session.execute(select(ReminderLog))).scalars().all())
        assert logs == []
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_reminder_route_mixed_results(
    client,
    reminder_db_session: AsyncSession,
    reminder_fixture_data: dict[str, uuid.UUID],
) -> None:
    fake_email_service = FakeEmailService()

    async def override_get_db():
        yield reminder_db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_email_service] = lambda: fake_email_service

    try:
        response = await client.post(
            "/api/v1/dashboard/reminders",
            json={
                "business_id": str(reminder_fixture_data["business_a_id"]),
                "invoice_ids": [
                    str(reminder_fixture_data["sent_invoice_id"]),
                    str(reminder_fixture_data["no_email_invoice_id"]),
                    str(reminder_fixture_data["other_business_invoice_id"]),
                ],
            },
        )
        assert response.status_code == 200
        body = response.json()["result"]
        assert len(body["sent"]) == 1
        assert [item["reason"] for item in body["skipped"]] == [
            "No email on file for this customer",
            "Invoice not found or does not belong to this business",
        ]

        logs = list(
            (
                await reminder_db_session.execute(
                    select(ReminderLog).order_by(ReminderLog.sent_at.asc())
                )
            )
            .scalars()
            .all()
        )
        assert len(logs) == 1
        assert logs[0].status == "sent"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_reminder_route_smtp_failure_logs_failed_rows(
    client,
    reminder_db_session: AsyncSession,
    reminder_fixture_data: dict[str, uuid.UUID],
) -> None:
    fake_email_service = FakeEmailService({"alice@example.com"})

    async def override_get_db():
        yield reminder_db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_email_service] = lambda: fake_email_service

    try:
        response = await client.post(
            "/api/v1/dashboard/reminders",
            json={
                "business_id": str(reminder_fixture_data["business_a_id"]),
                "invoice_ids": [str(reminder_fixture_data["sent_invoice_id"])],
            },
        )
        assert response.status_code == 200
        body = response.json()["result"]
        assert body["sent"] == []
        assert body["skipped"][0]["reason"] == "SMTP failed for alice@example.com"

        logs = list((await reminder_db_session.execute(select(ReminderLog))).scalars().all())
        assert len(logs) == 1
        assert logs[0].status == "failed"
        assert logs[0].error_message == "SMTP failed for alice@example.com"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_reminder_route_validation_and_not_found_errors(
    client,
    reminder_db_session: AsyncSession,
) -> None:
    fake_email_service = FakeEmailService()

    async def override_get_db():
        yield reminder_db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_email_service] = lambda: fake_email_service

    try:
        missing_business = await client.post(
            "/api/v1/dashboard/reminders",
            json={"invoice_ids": [str(uuid.uuid4())]},
        )
        assert missing_business.status_code == 422

        empty_ids = await client.post(
            "/api/v1/dashboard/reminders",
            json={"business_id": str(uuid.uuid4()), "invoice_ids": []},
        )
        assert empty_ids.status_code == 422

        invalid_uuid = await client.post(
            "/api/v1/dashboard/reminders",
            json={"business_id": str(uuid.uuid4()), "invoice_ids": ["bad-uuid"]},
        )
        assert invalid_uuid.status_code == 422

        not_found = await client.post(
            "/api/v1/dashboard/reminders",
            json={"business_id": str(uuid.uuid4()), "invoice_ids": [str(uuid.uuid4())]},
        )
        assert not_found.status_code == 404
        assert not_found.json()["error"] == "Business not found"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_reminder_openapi_includes_route(client) -> None:
    response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    assert "/api/v1/dashboard/reminders" in response.json()["paths"]
