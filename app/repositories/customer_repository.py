from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Customer


class CustomerRepositoryInterface(ABC):
    @abstractmethod
    async def get_customer_by_id(self, customer_id: UUID) -> Optional[Customer]:
        pass

    @abstractmethod
    async def create_customer(self, customer: Customer) -> Customer:
        pass

    @abstractmethod
    async def update_customer(self, customer_id: UUID, customer: Customer) -> Customer:
        pass

    @abstractmethod
    async def delete_customer(self, customer_id: UUID) -> None:
        pass

    @abstractmethod
    async def list_customers(self) -> List[Customer]:
        pass


class CustomerRepository(CustomerRepositoryInterface):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_customer_by_id(self, customer_id: UUID) -> Optional[Customer]:
        result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        return result.scalars().first()

    async def create_customer(self, customer: Customer) -> Customer:
        self.db.add(customer)
        await self.db.commit()
        await self.db.refresh(customer)
        return customer

    async def update_customer(self, customer_id: UUID, customer: Customer) -> Customer:
        existing = await self.get_customer_by_id(customer_id)
        if not existing:
            raise ValueError(f"Customer with id {customer_id} not found")

        for field, value in vars(customer).items():
            if not field.startswith("_"):  # skip SQLAlchemy internal attrs
                setattr(existing, field, value)

        await self.db.commit()
        await self.db.refresh(existing)
        return existing

    async def delete_customer(self, customer_id: UUID) -> None:
        existing = await self.get_customer_by_id(customer_id)
        if not existing:
            raise ValueError(f"Customer with id {customer_id} not found")

        await self.db.delete(existing)
        await self.db.commit()

    async def list_customers(self) -> List[Customer]:
        result = await self.db.execute(select(Customer))
        return list(result.scalars().all())