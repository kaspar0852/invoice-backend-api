from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import Business
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.payment import Payment, PaymentStatus
from app.models.reminder_log import ReminderLog
from app.schemas.dashboard_dto import round_money


@dataclass
class ReminderInvoiceRecord:
    invoice_id: UUID
    business_id: UUID
    business_name: str
    invoice_number: str
    status: str
    total_amount: Decimal
    remaining_balance: Decimal
    due_date: date | None
    customer_id: UUID
    customer_name: str
    customer_email: str | None
    customer_phone: str | None


class ReminderRepositoryInterface(ABC):
    @abstractmethod
    async def business_exists(self, business_id: UUID) -> bool:
        pass

    @abstractmethod
    async def get_invoices_for_reminder(
        self,
        business_id: UUID,
        invoice_ids: list[UUID],
    ) -> list[ReminderInvoiceRecord]:
        pass

    @abstractmethod
    async def log_reminder(
        self,
        invoice_id: UUID,
        business_id: UUID,
        recipient_email: str,
        channel: str,
        status: str,
        error_message: str | None = None,
    ) -> ReminderLog:
        pass


class ReminderRepository(ReminderRepositoryInterface):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def business_exists(self, business_id: UUID) -> bool:
        result = await self.db.execute(
            select(Business.id).where(Business.id == business_id)
        )
        return result.scalar_one_or_none() is not None

    async def get_invoices_for_reminder(
        self,
        business_id: UUID,
        invoice_ids: list[UUID],
    ) -> list[ReminderInvoiceRecord]:
        if not invoice_ids:
            return []

        settled_payments = (
            select(
                Payment.invoice_id.label("invoice_id"),
                func.coalesce(func.sum(Payment.amount), 0).label("settled_total"),
            )
            .where(
                Payment.business_id == business_id,
                Payment.status == PaymentStatus.SETTLED,
            )
            .group_by(Payment.invoice_id)
            .subquery()
        )

        remaining_balance = (
            Invoice.total_amount - func.coalesce(settled_payments.c.settled_total, 0)
        ).label("remaining_balance")

        stmt = (
            select(
                Invoice.id.label("invoice_id"),
                Invoice.business_id,
                Business.name.label("business_name"),
                Invoice.invoice_number,
                Invoice.status,
                Invoice.total_amount,
                remaining_balance,
                Invoice.due_date,
                Customer.id.label("customer_id"),
                Customer.name.label("customer_name"),
                Customer.email.label("customer_email"),
                Customer.phone.label("customer_phone"),
            )
            .select_from(Invoice)
            .join(Customer, Customer.id == Invoice.customer_id)
            .join(Business, Business.id == Invoice.business_id)
            .outerjoin(settled_payments, settled_payments.c.invoice_id == Invoice.id)
            .where(
                Invoice.business_id == business_id,
                Invoice.id.in_(invoice_ids),
            )
        )
        result = await self.db.execute(stmt)

        return [
            ReminderInvoiceRecord(
                invoice_id=row["invoice_id"],
                business_id=row["business_id"],
                business_name=row["business_name"],
                invoice_number=row["invoice_number"],
                status=row["status"].value,
                total_amount=round_money(row["total_amount"]),
                remaining_balance=round_money(row["remaining_balance"]),
                due_date=row["due_date"],
                customer_id=row["customer_id"],
                customer_name=row["customer_name"],
                customer_email=row["customer_email"],
                customer_phone=row["customer_phone"],
            )
            for row in result.mappings().all()
        ]

    async def log_reminder(
        self,
        invoice_id: UUID,
        business_id: UUID,
        recipient_email: str,
        channel: str,
        status: str,
        error_message: str | None = None,
    ) -> ReminderLog:
        reminder_log = ReminderLog(
            invoice_id=invoice_id,
            business_id=business_id,
            recipient_email=recipient_email,
            channel=channel,
            status=status,
            error_message=error_message,
        )
        self.db.add(reminder_log)
        await self.db.commit()
        await self.db.refresh(reminder_log)
        return reminder_log
