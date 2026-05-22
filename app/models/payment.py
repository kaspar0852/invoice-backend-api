import enum
import uuid
from datetime import datetime, date
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, Numeric, func, Uuid, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class PaymentMethod(str, enum.Enum):
    CASH = "Cash"
    BANK = "Bank"
    MOBILE = "Mobile"
    CHEQUE = "Cheque"

class PaymentStatus(str, enum.Enum):
    PENDING = "Pending"
    SETTLED = "Settled"
    FAILED = "Failed"
    REFUNDED = "Refunded"   


PAYMENT_METHOD_ENUM = Enum(
    PaymentMethod,
    name="payment_method_enum",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)

PAYMENT_STATUS_ENUM = Enum(
    PaymentStatus,
    name="payment_status_enum",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        "Id",
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        "InvoiceId",
        Uuid(as_uuid=True),
        ForeignKey("invoices.Id", ondelete="CASCADE"),
        nullable=False,
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        "BusinessId",
        Uuid(as_uuid=True),
        ForeignKey("businesses.Id", ondelete="CASCADE"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        "Amount",
        Numeric(12, 2),
        nullable=False,
    )
    payment_date: Mapped[date] = mapped_column(
        "PaymentDate",
        Date,
        nullable=False,
    )
    payment_method: Mapped[PaymentMethod] = mapped_column(
        "PaymentMethod",
        PAYMENT_METHOD_ENUM,
        nullable=False,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        "Status",
        PAYMENT_STATUS_ENUM,
        nullable=False,
        default=PaymentStatus.PENDING,
        server_default="Pending",
    )
    reference: Mapped[Optional[str]] = mapped_column(
        "Reference",
        String(255),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        "CreatedAt",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
