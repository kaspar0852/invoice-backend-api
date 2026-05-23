import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ReminderLog(Base):
    __tablename__ = "reminder_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        "Id",
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
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
    recipient_email: Mapped[str] = mapped_column(
        "RecipientEmail",
        String(255),
        nullable=False,
    )
    channel: Mapped[str] = mapped_column(
        "Channel",
        String(50),
        nullable=False,
    )
    sent_at: Mapped[datetime] = mapped_column(
        "SentAt",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        "Status",
        String(50),
        nullable=False,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        "ErrorMessage",
        Text,
        nullable=True,
    )
