from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, Field, field_serializer


MONEY_QUANTUM = Decimal("0.01")


def round_money(value: Decimal) -> Decimal:
    return Decimal(str(value)).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


MoneyAmount = Annotated[
    Decimal,
    BeforeValidator(round_money),
    Field(decimal_places=2),
]


class PeriodInfo(BaseModel):
    start_date: date
    end_date: date
    label: str


class MetricsSummary(BaseModel):
    revenue: MoneyAmount
    vat_liability: MoneyAmount
    outstanding_receivables: MoneyAmount

    @field_serializer(
        "revenue",
        "vat_liability",
        "outstanding_receivables",
        when_used="json",
    )
    def serialize_money(self, value: Decimal) -> float:
        return float(value)


class FinancialSummaryResponse(BaseModel):
    business_id: UUID
    period: PeriodInfo
    metrics: MetricsSummary


class OutstandingStatusFilter(str, enum.Enum):
    SENT = "Sent"
    PARTIAL = "Partial"
    OVERDUE = "Overdue"


class OutstandingInvoiceRow(BaseModel):
    invoice_id: UUID
    invoice_number: str
    status: OutstandingStatusFilter
    due_date: date | None
    aging_days: int | None
    total_amount: MoneyAmount
    remaining_balance: MoneyAmount
    customer_id: UUID
    customer_name: str
    customer_email: str | None
    customer_phone: str | None

    @field_serializer("total_amount", "remaining_balance", when_used="json")
    def serialize_money(self, value: Decimal) -> float:
        return float(value)


class OutstandingSummary(BaseModel):
    total_outstanding: MoneyAmount
    total_invoices: int

    @field_serializer("total_outstanding", when_used="json")
    def serialize_money(self, value: Decimal) -> float:
        return float(value)


class PaginationInfo(BaseModel):
    limit: int
    offset: int
    total: int


class OutstandingPaymentsResponse(BaseModel):
    business_id: UUID
    invoices: list[OutstandingInvoiceRow]
    summary: OutstandingSummary
    pagination: PaginationInfo
