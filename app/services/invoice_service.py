from datetime import date, datetime, timezone
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from fastapi import HTTPException, status

from app.models.invoice import Invoice, InvoiceStatus
from app.models.invoice_item import InvoiceItem
from app.repositories.invoice_repository import InvoiceRepositoryInterface
from app.schemas.invoice_dto import InvoiceCreate, InvoiceUpdate, InvoiceRead


class InvoiceService:
    def __init__(self, repository: InvoiceRepositoryInterface):
        self.repository = repository

    async def generate_invoice_number(self, business_id: UUID) -> str:
        current_year = date.today().year
        prefix = f"INV-{current_year}-"
        latest = await self.repository.get_latest_invoice_number(business_id, prefix)
        
        if latest:
            try:
                # Extract suffix number
                suffix_part = latest[len(prefix):]
                sequence = int(suffix_part)
                next_seq = sequence + 1
            except ValueError:
                next_seq = 1
        else:
            next_seq = 1
            
        return f"{prefix}{next_seq:04d}"

    def calculate_invoice_totals(
        self,
        invoice_data: InvoiceCreate | InvoiceUpdate,
        existing_items: Optional[list] = None
    ) -> tuple[Decimal, Decimal, Decimal, Decimal]:
        """
        Calculates subtotal, vat_amount, discount_amount, and total_amount.
        Returns (subtotal, vat_amount, discount_amount, total_amount)
        """
        subtotal = Decimal("0.00")
        vat_amount = Decimal("0.00")
        
        # If updating and items are not provided, we reuse existing items' totals
        items_source = invoice_data.items
        if items_source is None and existing_items is not None:
            for item in existing_items:
                line_total = Decimal(str(item.line_total))
                subtotal += line_total
                
                rate = Decimal(str(item.vat_rate)) if item.vat_rate is not None else Decimal("0.00")
                if rate > 0:
                    vat_amount += line_total * (rate / Decimal("100.00"))
        elif items_source is not None:
            for item in items_source:
                qty = Decimal(str(item.quantity))
                price = Decimal(str(item.unit_price))
                disc = Decimal(str(item.discount)) if item.discount is not None else Decimal("0.00")
                
                line_total = qty * price - disc
                if line_total < 0:
                    line_total = Decimal("0.00")
                
                subtotal += line_total
                
                rate = Decimal(str(item.vat_rate)) if item.vat_rate is not None else Decimal("0.00")
                if rate > 0:
                    vat_amount += line_total * (rate / Decimal("100.00"))

        # Calculate overall discount
        discount_amount = Decimal(str(invoice_data.discount_amount)) if invoice_data.discount_amount is not None else Decimal("0.00")
        
        total_amount = subtotal + vat_amount - discount_amount
        if total_amount < 0:
            total_amount = Decimal("0.00")
            
        TWO_PLACES = Decimal("0.01")
        return (
            subtotal.quantize(TWO_PLACES),
            vat_amount.quantize(TWO_PLACES),
            discount_amount.quantize(TWO_PLACES),
            total_amount.quantize(TWO_PLACES)
        )

    async def create_invoice(self, schema: InvoiceCreate) -> InvoiceRead:
        # Check uniqueness if number is custom-defined
        if schema.invoice_number:
            existing = await self.repository.get_by_invoice_number(schema.invoice_number)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invoice number '{schema.invoice_number}' already exists",
                )
            invoice_num = schema.invoice_number
        else:
            invoice_num = await self.generate_invoice_number(schema.business_id)

        subtotal, vat_amount, discount_amount, total_amount = self.calculate_invoice_totals(schema)

        # Build items
        db_items = []
        for item in schema.items:
            qty = Decimal(str(item.quantity))
            price = Decimal(str(item.unit_price))
            disc = Decimal(str(item.discount)) if item.discount is not None else Decimal("0.00")
            line_total = qty * price - disc
            if line_total < 0:
                line_total = Decimal("0.00")
            line_total = line_total.quantize(Decimal("0.01"))

            db_items.append(
                InvoiceItem(
                    product_name=item.product_name,
                    quantity=qty,
                    unit_price=price,
                    vat_rate=item.vat_rate,
                    discount=item.discount,
                    line_total=line_total
                )
            )

        invoice = Invoice(
            business_id=schema.business_id,
            customer_id=schema.customer_id,
            invoice_number=invoice_num,
            status=schema.status,
            subtotal=subtotal,
            vat_amount=vat_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            due_date=schema.due_date,
            notes=schema.notes,
            created_by=schema.created_by,
            items=db_items
        )

        created = await self.repository.create_invoice(invoice)
        return InvoiceRead.model_validate(created)

    async def get_invoice_by_id(self, invoice_id: UUID) -> InvoiceRead:
        invoice = await self.repository.get_by_id(invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        return InvoiceRead.model_validate(invoice)

    async def list_invoices(self, business_id: Optional[UUID] = None) -> List[InvoiceRead]:
        invoices = await self.repository.list_invoices(business_id)
        return [InvoiceRead.model_validate(inv) for inv in invoices]

    async def list_customer_invoices(
        self,
        customer_id: UUID,
        business_id: UUID,
    ) -> List[InvoiceRead]:
        invoices = await self.repository.list_customer_invoices(customer_id, business_id)
        return [InvoiceRead.model_validate(inv) for inv in invoices]

    async def update_invoice(self, invoice_id: UUID, schema: InvoiceUpdate) -> InvoiceRead:
        invoice = await self.repository.get_by_id(invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )

        # A finalized/cancelled invoice cannot be updated
        if invoice.status != InvoiceStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only draft invoices can be modified (current status: {invoice.status.value})"
            )

        if schema.invoice_number and schema.invoice_number != invoice.invoice_number:
            existing = await self.repository.get_by_invoice_number(schema.invoice_number)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invoice number '{schema.invoice_number}' already exists",
                )
            invoice.invoice_number = schema.invoice_number

        if schema.customer_id is not None:
            invoice.customer_id = schema.customer_id

        if schema.due_date is not None:
            invoice.due_date = schema.due_date

        if schema.notes is not None:
            invoice.notes = schema.notes

        if schema.status is not None:
            invoice.status = schema.status

        # Re-calculate totals
        subtotal, vat_amount, discount_amount, total_amount = self.calculate_invoice_totals(
            schema,
            existing_items=invoice.items
        )
        invoice.subtotal = subtotal
        invoice.vat_amount = vat_amount
        invoice.discount_amount = discount_amount
        invoice.total_amount = total_amount

        # Update items if provided
        if schema.items is not None:
            db_items = []
            for item in schema.items:
                qty = Decimal(str(item.quantity))
                price = Decimal(str(item.unit_price))
                disc = Decimal(str(item.discount)) if item.discount is not None else Decimal("0.00")
                line_total = qty * price - disc
                if line_total < 0:
                    line_total = Decimal("0.00")
                line_total = line_total.quantize(Decimal("0.01"))

                db_items.append(
                    InvoiceItem(
                        product_name=item.product_name,
                        quantity=qty,
                        unit_price=price,
                        vat_rate=item.vat_rate,
                        discount=item.discount,
                        line_total=line_total
                    )
                )
            invoice.items = db_items

        updated = await self.repository.update_invoice(invoice)
        return InvoiceRead.model_validate(updated)

    async def finalize_invoice(self, invoice_id: UUID) -> InvoiceRead:
        invoice = await self.repository.get_by_id(invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )

        if invoice.status != InvoiceStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invoice is already finalized or cannot be transitioned from status: {invoice.status.value}"
            )

        invoice.status = InvoiceStatus.SENT
        updated = await self.repository.update_invoice(invoice)
        return InvoiceRead.model_validate(updated)

    async def delete_invoice(self, invoice_id: UUID) -> None:
        invoice = await self.repository.get_by_id(invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )

        # Allow deleting any invoice, or restrict to draft. Standard practice allows deleting draft,
        # but let's allow general deletion or restrict depending on spec.
        # Since the acceptance criteria doesn't specify, we'll allow deleting draft invoices only or all.
        # Restricting deletion of non-draft is a good professional rule of thumb.
        if invoice.status != InvoiceStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only draft invoices can be deleted (current status: {invoice.status.value})"
            )

        await self.repository.delete_invoice(invoice_id)
