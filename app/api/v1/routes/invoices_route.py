from datetime import date
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.repositories.invoice_repository import InvoiceRepository
from app.schemas.invoice_dto import InvoiceRead, InvoiceCreate, InvoiceUpdate, InvoiceStatusUpdate, InvoiceSearchResponse
from app.models.invoice import InvoiceStatus
from app.services.invoice_service import InvoiceService
from app.core.route_class import StandardAPIRoute

router = APIRouter(route_class=StandardAPIRoute)


def get_invoice_service(
    db: AsyncSession = Depends(get_db)
) -> InvoiceService:
    repository = InvoiceRepository(db)
    return InvoiceService(repository)


@router.post(
    "/",
    response_model=InvoiceRead,
    status_code=status.HTTP_201_CREATED
)
async def create_invoice(
    schema: InvoiceCreate,
    service: InvoiceService = Depends(get_invoice_service),
) -> InvoiceRead:
    return await service.create_invoice(schema)


@router.get("/", response_model=InvoiceSearchResponse)
async def search_invoices(
    business_id: uuid.UUID = Query(...),
    customer_id: Optional[uuid.UUID] = Query(default=None),
    invoice_number: Optional[str] = Query(default=None, max_length=100),
    customer_name: Optional[str] = Query(default=None, max_length=255),
    status: Optional[List[InvoiceStatus]] = Query(default=None),
    created_after: Optional[date] = Query(default=None),
    created_before: Optional[date] = Query(default=None),
    due_after: Optional[date] = Query(default=None),
    due_before: Optional[date] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: InvoiceService = Depends(get_invoice_service),
) -> InvoiceSearchResponse:
    return await service.search_invoices(
        business_id=business_id,
        customer_id=customer_id,
        invoice_number=invoice_number,
        customer_name=customer_name,
        status=status,
        created_after=created_after,
        created_before=created_before,
        due_after=due_after,
        due_before=due_before,
        limit=limit,
        offset=offset,
    )


@router.get("/customer/{customer_id}", response_model=List[InvoiceRead])
async def list_customer_invoices(
    customer_id: uuid.UUID,
    business_id: uuid.UUID = Query(...),
    service: InvoiceService = Depends(get_invoice_service),
) -> List[InvoiceRead]:
    return await service.list_customer_invoices(customer_id, business_id)

@router.get("/{invoice_id}", response_model=InvoiceRead)
async def get_invoice(
    invoice_id: uuid.UUID,
    service: InvoiceService = Depends(get_invoice_service),
) -> InvoiceRead:
    return await service.get_invoice_by_id(invoice_id)


@router.put("/{invoice_id}", response_model=InvoiceRead)
async def update_invoice(
    invoice_id: uuid.UUID,
    schema: InvoiceUpdate,
    service: InvoiceService = Depends(get_invoice_service),
) -> InvoiceRead:
    return await service.update_invoice(invoice_id, schema)


@router.post("/{invoice_id}/finalize", response_model=InvoiceRead)
async def finalize_invoice(
    invoice_id: uuid.UUID,
    service: InvoiceService = Depends(get_invoice_service),
) -> InvoiceRead:
    return await service.finalize_invoice(invoice_id)


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_invoice(
    invoice_id: uuid.UUID,
    service: InvoiceService = Depends(get_invoice_service),
) -> None:
    await service.delete_invoice(invoice_id)


@router.patch("/{invoice_id}/status", response_model=InvoiceRead)
async def update_invoice_status(
    invoice_id: uuid.UUID,
    schema: InvoiceStatusUpdate,
    service: InvoiceService = Depends(get_invoice_service),
) -> InvoiceRead:
    return await service.update_status(invoice_id, schema.status)


@router.post("/{invoice_id}/check-overdue", response_model=InvoiceRead)
async def check_and_mark_overdue(
    invoice_id: uuid.UUID,
    service: InvoiceService = Depends(get_invoice_service),
) -> InvoiceRead:
    return await service.check_and_mark_overdue(invoice_id)

