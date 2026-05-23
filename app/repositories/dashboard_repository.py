from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import Business
from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment, PaymentStatus
from app.schemas.dashboard_dto import OutstandingInvoiceRow, OutstandingStatusFilter, round_money


class DashboardRepositoryInterface(ABC):
    @abstractmethod
    async def business_exists(self, business_id: UUID) -> bool:
        pass

    @abstractmethod
    async def get_revenue(self, business_id: UUID, start_date: date, end_date: date) -> Decimal:
        pass

    @abstractmethod
    async def get_vat_liability(self, business_id: UUID, start_date: date, end_date: date) -> Decimal:
        pass

    @abstractmethod
    async def get_outstanding_receivables(self, business_id: UUID) -> Decimal:
        pass

    @abstractmethod
    async def get_outstanding_invoices(
        self,
        business_id: UUID,
        status: OutstandingStatusFilter | None = None,
        customer_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[OutstandingInvoiceRow]:
        pass

    @abstractmethod
    async def get_outstanding_totals(
        self,
        business_id: UUID,
        status: OutstandingStatusFilter | None = None,
        customer_id: UUID | None = None,
    ) -> tuple[Decimal, int]:
        pass


class DashboardRepository(DashboardRepositoryInterface):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def business_exists(self, business_id: UUID) -> bool:
        result = await self.db.execute(
            select(Business.id).where(Business.id == business_id)
        )
        return result.scalar_one_or_none() is not None

    async def get_revenue(self, business_id: UUID, start_date: date, end_date: date) -> Decimal:
        stmt = select(
            func.coalesce(func.sum(Payment.amount), 0)
        ).where(
            Payment.business_id == business_id,
            Payment.status == PaymentStatus.SETTLED,
            Payment.payment_date >= start_date,
            Payment.payment_date <= end_date,
        )
        result = await self.db.execute(stmt)
        return round_money(result.scalar_one())

    async def get_vat_liability(self, business_id: UUID, start_date: date, end_date: date) -> Decimal:
        proportional_vat = Payment.amount * (Invoice.vat_amount / Invoice.total_amount)
        stmt = (
            select(func.coalesce(func.sum(proportional_vat), 0))
            .select_from(Payment)
            .join(Invoice, Invoice.id == Payment.invoice_id)
            .where(
                Payment.business_id == business_id,
                Payment.status == PaymentStatus.SETTLED,
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date,
                Invoice.total_amount != 0,
            )
        )
        result = await self.db.execute(stmt)
        return round_money(result.scalar_one())

    async def get_outstanding_receivables(self, business_id: UUID) -> Decimal:
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

        stmt = (
            select(
                func.coalesce(
                    func.sum(
                        Invoice.total_amount - func.coalesce(settled_payments.c.settled_total, 0)
                    ),
                    0,
                )
            )
            .select_from(Invoice)
            .outerjoin(settled_payments, settled_payments.c.invoice_id == Invoice.id)
            .where(
                Invoice.business_id == business_id,
                Invoice.status.in_(
                    [
                        InvoiceStatus.SENT,
                        InvoiceStatus.PARTIAL,
                        InvoiceStatus.OVERDUE,
                    ]
                ),
            )
        )
        result = await self.db.execute(stmt)
        return round_money(result.scalar_one())

    def _build_settled_payments_subquery(self, business_id: UUID):
        return (
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

    def _build_outstanding_invoice_base_query(
        self,
        business_id: UUID,
        status: OutstandingStatusFilter | None = None,
        customer_id: UUID | None = None,
    ):
        settled_payments = self._build_settled_payments_subquery(business_id)
        remaining_balance = (
            Invoice.total_amount - func.coalesce(settled_payments.c.settled_total, 0)
        ).label("remaining_balance")

        stmt = (
            select(
                Invoice.id.label("invoice_id"),
                Invoice.invoice_number,
                Invoice.status,
                Invoice.due_date,
                Invoice.total_amount,
                remaining_balance,
                Customer.id.label("customer_id"),
                Customer.name.label("customer_name"),
                Customer.email.label("customer_email"),
                Customer.phone.label("customer_phone"),
            )
            .select_from(Invoice)
            .join(Customer, Customer.id == Invoice.customer_id)
            .outerjoin(settled_payments, settled_payments.c.invoice_id == Invoice.id)
            .where(
                Invoice.business_id == business_id,
                Invoice.status.in_(
                    [
                        InvoiceStatus.SENT,
                        InvoiceStatus.PARTIAL,
                        InvoiceStatus.OVERDUE,
                    ]
                ),
                remaining_balance > 0,
            )
        )

        if status is not None:
            stmt = stmt.where(Invoice.status == InvoiceStatus(status.value))

        if customer_id is not None:
            stmt = stmt.where(Invoice.customer_id == customer_id)

        return stmt, remaining_balance

    def _calculate_aging_days(self, due_date: date | None) -> int | None:
        if due_date is None:
            return None
        return (date.today() - due_date).days

    async def get_outstanding_invoices(
        self,
        business_id: UUID,
        status: OutstandingStatusFilter | None = None,
        customer_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[OutstandingInvoiceRow]:
        stmt, _ = self._build_outstanding_invoice_base_query(
            business_id=business_id,
            status=status,
            customer_id=customer_id,
        )

        stmt = stmt.order_by(Invoice.due_date.asc().nulls_last()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)

        rows = []
        for record in result.mappings().all():
            rows.append(
                OutstandingInvoiceRow(
                    invoice_id=record["invoice_id"],
                    invoice_number=record["invoice_number"],
                    status=OutstandingStatusFilter(record["status"].value),
                    due_date=record["due_date"],
                    aging_days=self._calculate_aging_days(record["due_date"]),
                    total_amount=round_money(record["total_amount"]),
                    remaining_balance=round_money(record["remaining_balance"] or Decimal("0.00")),
                    customer_id=record["customer_id"],
                    customer_name=record["customer_name"],
                    customer_email=record["customer_email"],
                    customer_phone=record["customer_phone"],
                )
            )

        rows.sort(
            key=lambda row: (
                row.aging_days is None,
                -(row.aging_days if row.aging_days is not None else 0),
            )
        )
        return rows

    async def get_outstanding_totals(
        self,
        business_id: UUID,
        status: OutstandingStatusFilter | None = None,
        customer_id: UUID | None = None,
    ) -> tuple[Decimal, int]:
        stmt, remaining_balance = self._build_outstanding_invoice_base_query(
            business_id=business_id,
            status=status,
            customer_id=customer_id,
        )

        base_query = stmt.subquery()
        total_stmt = select(
            func.coalesce(func.sum(base_query.c.remaining_balance), 0),
            func.count(),
        )
        result = await self.db.execute(total_stmt)
        total_outstanding, total_invoices = result.one()
        return round_money(total_outstanding), int(total_invoices)
