from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Payment, Invoice
from app.models.payment import PaymentStatus


class PaymentRepositoryInterface(ABC):

    @abstractmethod
    async def get_by_customer_id(self, customer_id: UUID, business_id: UUID, status: Optional[str] = None) -> list[Payment]:
        pass


class PaymentRepository(PaymentRepositoryInterface):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_customer_id(self, customer_id: UUID, business_id: UUID, status: Optional[PaymentStatus] = None) -> list[Payment]:
        stmt = (
            select(Payment)
            .join(Invoice, Invoice.id == Payment.invoice_id)
            .where(
                Invoice.customer_id == customer_id,
                Invoice.business_id == business_id
            )
        )

        if status is not None:
            stmt = stmt.where(Payment.status == status)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

