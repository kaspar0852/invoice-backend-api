import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, func, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"

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
    name: Mapped[str] = mapped_column(
        "Name",
        String(255),
        nullable=False,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        "Phone",
        String(50),
        nullable=True,
    )
    email: Mapped[Optional[str]] = mapped_column(
        "Email",
        String(255),
        nullable=True,
    )
    address: Mapped[Optional[str]] = mapped_column(
        "Address",
        String(500),
        nullable=True,
    )
    vat_number: Mapped[Optional[str]] = mapped_column(
        "VatNumber",
        String(100),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        "CreatedAt",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
