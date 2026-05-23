import enum
import uuid
from datetime import datetime, date
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, Numeric, func, Uuid, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.invoice_item import InvoiceItem


class InvoiceStatus(str, enum.Enum):
    DRAFT = "Draft"
    SENT = "Sent"
    PAID = "Paid"
    PARTIAL = "Partial"
    OVERDUE = "Overdue"
    CANCELLED = "Cancelled"


INVOICE_STATUS_ENUM = Enum(
    InvoiceStatus,
    name="invoice_status_enum",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        "Id",
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        "BusinessId",
        Uuid(as_uuid=True),
        ForeignKey("businesses.Id", ondelete="CASCADE"),
        nullable=False,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        "CustomerId",
        Uuid(as_uuid=True),
        ForeignKey("customers.Id", ondelete="CASCADE"),
        nullable=False,
    )
    invoice_number: Mapped[str] = mapped_column(
        "InvoiceNumber",
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    status: Mapped[InvoiceStatus] = mapped_column(
        "Status",
        INVOICE_STATUS_ENUM,
        default=InvoiceStatus.DRAFT,
        nullable=False,
    )
    subtotal: Mapped[Decimal] = mapped_column(
        "Subtotal",
        Numeric(12, 2),
        nullable=False,
    )
    vat_amount: Mapped[Decimal] = mapped_column(
        "VatAmount",
        Numeric(12, 2),
        nullable=False,
    )
    discount_amount: Mapped[Optional[Decimal]] = mapped_column(
        "DiscountAmount",
        Numeric(12, 2),
        nullable=True,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        "TotalAmount",
        Numeric(12, 2),
        nullable=False,
    )
    due_date: Mapped[Optional[date]] = mapped_column(
        "DueDate",
        Date,
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        "Notes",
        String(1000),
        nullable=True,
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        "CreatedBy",
        Uuid(as_uuid=True),
        ForeignKey("users.Id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        "CreatedAt",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    items: Mapped[list["InvoiceItem"]] = relationship(
        "InvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
