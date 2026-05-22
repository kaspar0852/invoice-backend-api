from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from typing import Optional
from uuid import UUID
from decimal import Decimal
from app.models.payment import PaymentMethod, PaymentStatus

class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID
    business_id: UUID
    amount: Decimal
    payment_date: date
    payment_method: PaymentMethod
    status: PaymentStatus
    reference: Optional[str] = None
    created_at: datetime
