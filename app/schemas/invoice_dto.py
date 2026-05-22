from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime, date
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from app.models.invoice import InvoiceStatus


class InvoiceItemBase(BaseModel):
    product_name: str = Field(..., max_length=255)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    vat_rate: Optional[Decimal] = Field(default=None, ge=0)
    discount: Optional[Decimal] = Field(default=None, ge=0)

    @field_validator("product_name")
    @classmethod
    def validate_product_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Product name cannot be empty")
        return stripped


class InvoiceItemCreate(InvoiceItemBase):
    pass


class InvoiceItemRead(InvoiceItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID
    line_total: Decimal


class InvoiceBase(BaseModel):
    business_id: UUID
    customer_id: UUID
    invoice_number: Optional[str] = Field(default=None, max_length=100)
    status: InvoiceStatus = InvoiceStatus.DRAFT
    discount_amount: Optional[Decimal] = Field(default=None, ge=0)
    due_date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=1000)
    created_by: Optional[UUID] = None


class InvoiceCreate(InvoiceBase):
    items: List[InvoiceItemCreate] = Field(..., min_length=1)


class InvoiceUpdate(BaseModel):
    customer_id: Optional[UUID] = None
    invoice_number: Optional[str] = Field(default=None, max_length=100)
    status: Optional[InvoiceStatus] = None
    discount_amount: Optional[Decimal] = Field(default=None, ge=0)
    due_date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=1000)
    items: Optional[List[InvoiceItemCreate]] = None


class InvoiceRead(InvoiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subtotal: Decimal
    vat_amount: Decimal
    total_amount: Decimal
    created_at: datetime
    items: List[InvoiceItemRead]
