from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.invoice import Invoice


class InvoiceRepositoryInterface(ABC):
    @abstractmethod
    async def get_by_id(self, invoice_id: UUID) -> Optional[Invoice]:
        pass

    @abstractmethod
    async def get_by_invoice_number(self, invoice_number: str) -> Optional[Invoice]:
        pass

    @abstractmethod
    async def get_latest_invoice_number(
        self, business_id: UUID, prefix: str
    ) -> Optional[str]:
        pass

    @abstractmethod
    async def create_invoice(self, invoice: Invoice) -> Invoice:
        pass

    @abstractmethod
    async def update_invoice(self, invoice: Invoice) -> Invoice:
        pass

    @abstractmethod
    async def list_invoices(self, business_id: Optional[UUID] = None) -> List[Invoice]:
        pass

    @abstractmethod
    async def list_customer_invoices(self, customer_id: UUID, business_id: UUID, valid_statuses: Optional[List[str]] = None) -> List[Invoice]:
        pass

    @abstractmethod
    async def delete_invoice(self, invoice_id: UUID) -> None:
        pass


class InvoiceRepository(InvoiceRepositoryInterface):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, invoice_id: UUID) -> Optional[Invoice]:
        result = await self.db.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        return result.scalars().first()

    async def get_by_invoice_number(self, invoice_number: str) -> Optional[Invoice]:
        result = await self.db.execute(
            select(Invoice).where(Invoice.invoice_number == invoice_number)
        )
        return result.scalars().first()

    async def get_latest_invoice_number(
        self, business_id: UUID, prefix: str
    ) -> Optional[str]:
        result = await self.db.execute(
            select(Invoice.invoice_number)
            .where(
                Invoice.business_id == business_id,
                Invoice.invoice_number.like(f"{prefix}%"),
            )
            .order_by(Invoice.invoice_number.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def create_invoice(self, invoice: Invoice) -> Invoice:
        self.db.add(invoice)
        await self.db.commit()
        await self.db.refresh(invoice)
        return invoice

    async def update_invoice(self, invoice: Invoice) -> Invoice:
        await self.db.commit()
        await self.db.refresh(invoice)
        return invoice

    async def list_invoices(self, business_id: Optional[UUID] = None) -> List[Invoice]:
        stmt = select(Invoice)
        if business_id is not None:
            stmt = stmt.where(Invoice.business_id == business_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # async def get_customer_invoices(self, customer_id: UUID, business_id: UUID) -> List[Invoice]:
    #     stmt = select(Invoice).where(
    #         Invoice.customer_id == customer_id,
    #         Invoice.business_id == business_id
    #     )
    #     result = await self.db.execute(stmt)
    #     return list(result.scalars().all())

    async def list_customer_invoices(self, customer_id: UUID, business_id: UUID, valid_statuses: Optional[List[str]] = None) -> List[Invoice]:
        stmt = select(Invoice).where(
            Invoice.customer_id == customer_id,
            Invoice.business_id == business_id
        )
        if valid_statuses:
            stmt = stmt.where(Invoice.status.in_(valid_statuses))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_invoice(self, invoice_id: UUID) -> None:
        invoice = await self.get_by_id(invoice_id)
        if invoice:
            await self.db.delete(invoice)
            await self.db.commit()
