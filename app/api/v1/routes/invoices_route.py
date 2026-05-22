from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.repositories.invoice_repository import InvoiceRepository
from app.schemas.invoice_dto import InvoiceRead, InvoiceCreate, InvoiceUpdate
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


@router.get("/", response_model=List[InvoiceRead])
async def list_invoices(
    business_id: Optional[uuid.UUID] = Query(default=None),
    service: InvoiceService = Depends(get_invoice_service),
) -> List[InvoiceRead]:
    return await service.list_invoices(business_id)

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
