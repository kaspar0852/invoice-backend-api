from uuid import UUID
from fastapi import HTTPException, status
from app.models.customer import Customer
from app.repositories.customer_repository import CustomerRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.payment_repository import PaymentRepository
from app.schemas.customer_dto import CustomerRead, CustomerUpdate, CustomerCreate, CustomerBalance, CustomerTransactionHistory
from app.schemas.invoice_dto import InvoiceRead
from app.schemas.payment_dto import PaymentRead
from app.models.invoice import InvoiceStatus
from app.models.payment import PaymentStatus
from typing import List, Optional
from decimal import Decimal


class CustomerService:
    def __init__(self,
                 repository: CustomerRepository,
                 invoice_repository: InvoiceRepository,
                 payment_repository: PaymentRepository):
        self.repository = repository
        self.invoice_repository = invoice_repository
        self.payment_repository = payment_repository

    async def create_customer(
        self,
        customer_data: CustomerCreate
    ) -> CustomerRead:

        customer = Customer(
            business_id =customer_data.business_id,
            name = customer_data.first_name + " " + customer_data.last_name,
            email=customer_data.email,
            phone =customer_data.phone_number,
            address=customer_data.address,
            vat_number=customer_data.vat_number
        )

        created_customer = await self.repository.create_customer(customer)

        return CustomerRead.from_orm_model(created_customer)

    async def get_customer_by_id(
        self,
        customer_id: UUID
    ) -> CustomerRead:

        customer = await self.repository.get_customer_by_id(customer_id)

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )

        return CustomerRead.from_orm_model(customer)

    async def get_customer_by_id_and_business(
        self,
        customer_id: UUID,
        business_id: UUID
    ) -> CustomerRead:

        customer = await self.repository.get_customer_by_id_and_business(customer_id, business_id)

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )

        return CustomerRead.from_orm_model(customer)

    async def get_customer_invoices(
        self,
        customer_id: UUID,
        business_id: UUID
    ) -> List[InvoiceRead]:

        customer = await self.repository.get_customer_by_id_and_business(customer_id, business_id)

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )

        valid_statuses = [
            InvoiceStatus.SENT,
            InvoiceStatus.PARTIAL,
            InvoiceStatus.OVERDUE,
            InvoiceStatus.PAID
        ]
        invoices = await self.invoice_repository.list_customer_invoices(
            customer_id, business_id, valid_statuses
        )

        return [InvoiceRead.model_validate(inv) for inv in invoices]

    async def get_customer_payments(
        self,
        customer_id: UUID,
        business_id: UUID,
        sts: Optional[PaymentStatus]
    ) -> List[PaymentRead]:

        customer = await self.repository.get_customer_by_id_and_business(customer_id, business_id)

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )

        payments = await self.payment_repository.get_by_customer_id(
            customer_id, business_id, sts
        )

        return [PaymentRead.model_validate(p) for p in payments]

    async def calculate_customer_balance(
        self,
        customer_id: UUID,
        business_id: UUID
    ) -> CustomerBalance:

        customer = await self.repository.get_customer_by_id_and_business(customer_id, business_id)

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )

        invoices = await self.invoice_repository.list_customer_invoices(customer_id, business_id)

        if not invoices:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found for customer"
            )

        total_invoiced = sum((inv.total_amount for inv in invoices), Decimal('0.00'))

        payments = await self.get_customer_payments(customer_id, business_id, PaymentStatus.SETTLED)
        total_paid = sum((p.amount for p in payments), Decimal('0.00'))

        outstanding_balance = total_invoiced - total_paid

        return CustomerBalance(
            customer_id=customer_id,
            outstanding_balance=outstanding_balance
        )

    async def get_customer_transaction_history(
        self,
        customer_id: UUID,
        business_id: UUID
    ) -> CustomerTransactionHistory:

        customer = await self.repository.get_customer_by_id_and_business(customer_id, business_id)

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )

        customer_dto = CustomerRead.from_orm_model(customer)

        invoices = await self.get_customer_invoices(customer_id, business_id)

        if not invoices:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found for customer"
            )

        total_invoiced = sum((inv.total_amount for inv in invoices), Decimal('0.00'))

        payments = await self.payment_repository.get_by_customer_id(customer_id, business_id)

        payment_dtos = [
            PaymentRead.model_validate(p)
            for p in payments
        ]

        settled_payments = [p for p in payments if p.status == PaymentStatus.SETTLED]
        total_paid = sum((p.amount for p in settled_payments), Decimal('0.00'))

        outstanding_balance = total_invoiced - total_paid

        return CustomerTransactionHistory(
            customer=customer_dto,
            invoices=invoices,
            payments=payment_dtos,
            total_invoiced=total_invoiced,
            total_paid=total_paid,
            outstanding_balance=outstanding_balance
        )

    async def get_all_customers(self) -> List[CustomerRead]:

        customers = await self.repository.list_customers()

        return [
            CustomerRead.from_orm_model(customer)
            for customer in customers
        ]

    async def update_customer(
        self,
        customer_id: UUID,
        customer_data: CustomerUpdate
    ) -> CustomerRead:

        customer = await self.repository.get_customer_by_id(customer_id)

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )

        update_data = customer_data.model_dump(
            exclude_unset=True
        )

        # Handle name splitting / merging
        first_name = update_data.pop("first_name", None)
        last_name = update_data.pop("last_name", None)
        if first_name is not None or last_name is not None:
            parts = customer.name.split(" ", 1)
            curr_first = parts[0] if len(parts) > 0 else ""
            curr_last = parts[1] if len(parts) > 1 else ""
            new_first = first_name if first_name is not None else curr_first
            new_last = last_name if last_name is not None else curr_last
            customer.name = f"{new_first} {new_last}".strip()

        # Handle phone_number to phone mapping
        if "phone_number" in update_data:
            customer.phone = update_data.pop("phone_number")

        # Map other fields
        for field, value in update_data.items():
            setattr(customer, field, value)

        updated_customer = await self.repository.update_customer(customer_id, customer)

        return CustomerRead.from_orm_model(updated_customer)

    async def delete_customer(
        self,
        customer_id: UUID
    ) -> None:

        customer = await self.repository.get_customer_by_id(customer_id)

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )

        await self.repository.delete_customer(customer_id)
