from uuid import UUID

from pydantic import BaseModel, Field


class SendRemindersRequest(BaseModel):
    business_id: UUID
    invoice_ids: list[UUID] = Field(..., min_length=1)


class ReminderSentItem(BaseModel):
    invoice_id: UUID
    recipient_email: str
    customer_name: str


class ReminderSkippedItem(BaseModel):
    invoice_id: UUID
    reason: str


class SendRemindersResponse(BaseModel):
    sent: list[ReminderSentItem]
    skipped: list[ReminderSkippedItem]
