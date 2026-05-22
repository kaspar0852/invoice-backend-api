import uuid
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import String, Numeric, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.invoice import Invoice


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

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
    product_name: Mapped[str] = mapped_column(
        "ProductName",
        String(255),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        "Quantity",
        Numeric(12, 4),
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        "UnitPrice",
        Numeric(12, 2),
        nullable=False,
    )
    vat_rate: Mapped[Optional[Decimal]] = mapped_column(
        "VatRate",
        Numeric(5, 2),
        nullable=True,
    )
    discount: Mapped[Optional[Decimal]] = mapped_column(
        "Discount",
        Numeric(12, 2),
        nullable=True,
    )
    line_total: Mapped[Decimal] = mapped_column(
        "LineTotal",
        Numeric(12, 2),
        nullable=False,
    )

    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="items"
    )
