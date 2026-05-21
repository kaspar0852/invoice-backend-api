import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(
        "Id",
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        "Name",
        String(255),
        nullable=False,
    )
    vat_number: Mapped[Optional[str]] = mapped_column(
        "VatNumber",
        String(100),
        nullable=True,
    )
    pan_number: Mapped[Optional[str]] = mapped_column(
        "PanNumber",
        String(100),
        nullable=True,
    )
    address: Mapped[Optional[str]] = mapped_column(
        "Address",
        String(500),
        nullable=True,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        "Phone",
        String(50),
        nullable=True,
    )
    logo_url: Mapped[Optional[str]] = mapped_column(
        "LogoUrl",
        String(500),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        "CreatedAt",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
