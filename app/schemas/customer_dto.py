from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    EmailStr
)
from datetime import datetime
from typing import Optional
from uuid import UUID
import re


class CustomerBase(BaseModel):
    first_name: str = Field(..., max_length=255)
    last_name: str = Field(..., max_length=255)
    email: EmailStr
    phone_number: str = Field(..., max_length=20)
    address: Optional[str] = Field(default=None, max_length=255)
    vat_number: Optional[str] = Field(default=None, max_length=30)

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, value):
        value = value.strip()

        if len(value) < 2:
            raise ValueError("Name must be at least 2 characters")

        if not value.replace(" ", "").isalpha():
            raise ValueError("Name must contain only letters")

        return value.title()

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value):
        value = value.replace(" ", "")

        pattern = r"^\+?[0-9]{7,15}$"

        if not re.match(pattern, value):
            raise ValueError("Invalid phone number")

        return value


class CustomerCreate(CustomerBase):
    business_id: UUID


class CustomerUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, max_length=255)
    last_name: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=255)
    vat_number: Optional[str] = Field(default=None, max_length=30)


class CustomerRead(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    created_at: datetime

    @classmethod
    def from_orm_model(cls, customer) -> "CustomerRead":
        parts = customer.name.split(" ", 1)
        first_name = parts[0] if len(parts) > 0 else ""
        last_name = parts[1] if len(parts) > 1 else ""
        return cls(
            id=customer.id,
            business_id=customer.business_id,
            first_name=first_name,
            last_name=last_name,
            email=customer.email,
            phone_number=customer.phone or "",
            address=customer.address,
            vat_number=customer.vat_number,
            created_at=customer.created_at,
        )