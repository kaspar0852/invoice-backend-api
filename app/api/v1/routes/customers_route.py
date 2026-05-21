from typing import List
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer_dto import CustomerRead, CustomerCreate, CustomerUpdate
from app.services.customer_service import CustomerService

from app.core.route_class import StandardAPIRoute

router = APIRouter(route_class=StandardAPIRoute)

def get_customer_service(
    db: AsyncSession = Depends(get_db)
) -> CustomerService:
    repository = CustomerRepository(db)
    return CustomerService(repository)

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
    service: CustomerService = Depends(get_customer_service),
) -> CustomerRead:
    return await service.get_customer_by_id(customer_id)

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