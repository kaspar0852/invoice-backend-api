from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_dashboard_service, get_reminder_service
from app.core.route_class import StandardAPIRoute
from app.schemas.dashboard_dto import (
    FinancialSummaryResponse,
    OutstandingPaymentsResponse,
    OutstandingStatusFilter,
)
from app.schemas.reminder_dto import SendRemindersRequest, SendRemindersResponse
from app.services.dashboard_service import DashboardService
from app.services.reminder_service import ReminderService


router = APIRouter(route_class=StandardAPIRoute)


@router.get("/financial-summary", response_model=FinancialSummaryResponse)
async def get_financial_summary(
    business_id: UUID = Query(...),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> FinancialSummaryResponse:
    return await dashboard_service.get_financial_summary(
        business_id=business_id,
        user_id=None,  # TODO: replace with auth dependency
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/outstanding-payments", response_model=OutstandingPaymentsResponse)
async def get_outstanding_payments(
    business_id: UUID = Query(...),
    status: Optional[OutstandingStatusFilter] = Query(default=None),
    customer_id: Optional[UUID] = Query(default=None),
    limit: Optional[int] = Query(default=None, gt=0),
    offset: Optional[int] = Query(default=None, ge=0),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> OutstandingPaymentsResponse:
    return await dashboard_service.get_outstanding_payments(
        business_id=business_id,
        user_id=None,  # TODO: replace with auth dependency
        status_filter=status,
        customer_id=customer_id,
        limit=limit,
        offset=offset,
    )


@router.post("/reminders", response_model=SendRemindersResponse)
async def send_reminders(
    request: SendRemindersRequest,
    reminder_service: ReminderService = Depends(get_reminder_service),
) -> SendRemindersResponse:
    return await reminder_service.send_reminders(
        request=request,
        user_id=None,  # TODO: replace with auth dependency
    )
