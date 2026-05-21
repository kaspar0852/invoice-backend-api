from typing import List
from uuid import UUID
from fastapi import HTTPException, status
from app.models.customer import Customer
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer_dto import CustomerRead, CustomerUpdate, CustomerCreate


class CustomerService:
    def __init__(self, repository: CustomerRepository):
        self.repository = repository

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