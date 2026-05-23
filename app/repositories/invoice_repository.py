from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.invoice import Invoice, InvoiceStatus
from app.models.customer import Customer


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
    async def search_invoices(
        self,
        business_id: UUID,
        customer_id: Optional[UUID] = None,
        invoice_number: Optional[str] = None,
        customer_name: Optional[str] = None,
        status: Optional[List[InvoiceStatus]] = None,
        created_after: Optional[date] = None,
        created_before: Optional[date] = None,
        due_after: Optional[date] = None,
        due_before: Optional[date] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Invoice], int]:
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

    async def search_invoices(
        self,
        business_id: UUID,
        customer_id: Optional[UUID] = None,
        invoice_number: Optional[str] = None,
        customer_name: Optional[str] = None,
        status: Optional[List[InvoiceStatus]] = None,
        created_after: Optional[date] = None,
        created_before: Optional[date] = None,
        due_after: Optional[date] = None,
        due_before: Optional[date] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Invoice], int]:
        # Build base query and shared filter conditions
        conditions = [Invoice.business_id == business_id]

        if customer_id is not None:
            conditions.append(Invoice.customer_id == customer_id)
        if invoice_number is not None:
            conditions.append(Invoice.invoice_number.ilike(f"%{invoice_number}%"))
        if status is not None:
            conditions.append(Invoice.status.in_(status))
        if created_after is not None:
            conditions.append(Invoice.created_at >= created_after)
        if created_before is not None:
            conditions.append(Invoice.created_at <= created_before)
        if due_after is not None:
            conditions.append(Invoice.due_date >= due_after)
        if due_before is not None:
            conditions.append(Invoice.due_date <= due_before)

        needs_join = customer_name is not None

        # --- Count query ---
        count_stmt = select(func.count(Invoice.id)).where(*conditions)
        if needs_join:
            count_stmt = count_stmt.join(Customer, Invoice.customer_id == Customer.id)
            count_stmt = count_stmt.where(Customer.name.ilike(f"%{customer_name}%"))
        count_result = await self.db.execute(count_stmt)
        total_count = count_result.scalar_one()

        # --- Data query ---
        data_stmt = select(Invoice).where(*conditions)
        if needs_join:
            data_stmt = data_stmt.join(Customer, Invoice.customer_id == Customer.id)
            data_stmt = data_stmt.where(Customer.name.ilike(f"%{customer_name}%"))
        data_stmt = data_stmt.order_by(Invoice.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(data_stmt)
        return list(result.scalars().all()), total_count

    async def delete_invoice(self, invoice_id: UUID) -> None:
        invoice = await self.get_by_id(invoice_id)
        if invoice:
            await self.db.delete(invoice)
            await self.db.commit()
