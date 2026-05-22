from typing import List
import uuid

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.repositories.customer_repository import CustomerRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.payment_repository import PaymentRepository
from app.schemas.customer_dto import CustomerRead, CustomerCreate, CustomerUpdate, CustomerTransactionHistory, \
    CustomerBalance
from app.schemas.invoice_dto import InvoiceRead
from app.schemas.payment_dto import PaymentRead
from app.models.payment import PaymentStatus
from app.services.customer_service import CustomerService
from typing import Optional

from app.core.route_class import StandardAPIRoute

router = APIRouter(route_class=StandardAPIRoute)

def get_customer_service(
    db: AsyncSession = Depends(get_db)
) -> CustomerService:
    repository = CustomerRepository(db)
    invoice_repository = InvoiceRepository(db)
    payment_repository = PaymentRepository(db)
    return CustomerService(repository, invoice_repository, payment_repository)

@router.post(
    "/",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED
)
async def create_customer(
    schema: CustomerCreate,
    service: CustomerService = Depends(get_customer_service),
) -> CustomerRead:
    return await service.create_customer(schema)

@router.get("/", response_model=List[CustomerRead])
async def list_customers(
    service: CustomerService = Depends(get_customer_service),
) -> List[CustomerRead]:
    return await service.get_all_customers()

@router.get("/{customer_id}", response_model=CustomerRead)
async def get_customer(
    customer_id: uuid.UUID,
    business_id: uuid.UUID = Query(...),
    service: CustomerService = Depends(get_customer_service),
) -> CustomerRead:
    return await service.get_customer_by_id_and_business(customer_id, business_id)

@router.get("/{customer_id}/invoices", response_model=List[InvoiceRead])
async def get_customer_invoices(
    customer_id: uuid.UUID,
    business_id: uuid.UUID = Query(...),
    service: CustomerService = Depends(get_customer_service),
) -> List[InvoiceRead]:
    return await service.get_customer_invoices(customer_id, business_id)

@router.get("/{customer_id}/payments", response_model=List[PaymentRead])
async def get_customer_payments(
    customer_id: uuid.UUID,
    business_id: uuid.UUID = Query(...),
    status: Optional[PaymentStatus] = Query(None),
    service: CustomerService = Depends(get_customer_service),
) -> List[PaymentRead]:
    return await service.get_customer_payments(customer_id, business_id, status)

@router.get("/{customer_id}/balance", response_model=CustomerBalance)
async def get_customer_balance(
    customer_id: uuid.UUID,
    business_id: uuid.UUID = Query(...),
    service: CustomerService = Depends(get_customer_service),
) -> CustomerBalance:
    return await service.calculate_customer_balance(customer_id, business_id)

@router.get("/{customer_id}/transactions", response_model=CustomerTransactionHistory)
async def get_customer_transactions(
    customer_id: uuid.UUID,
    business_id: uuid.UUID = Query(...),
    service: CustomerService = Depends(get_customer_service),
) -> CustomerTransactionHistory:
    return await service.get_customer_transaction_history(customer_id, business_id)

@router.put("/{customer_id}", response_model=CustomerRead)
async def update_customer(
    customer_id: uuid.UUID,
    schema: CustomerUpdate,
    service: CustomerService = Depends(get_customer_service),
) -> CustomerRead:
    return await service.update_customer(customer_id, schema)

@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_customer(
    customer_id: uuid.UUID,
    service: CustomerService = Depends(get_customer_service),
) -> None:
    await service.delete_customer(customer_id)