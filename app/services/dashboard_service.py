from calendar import monthrange
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status

from app.repositories.dashboard_repository import DashboardRepositoryInterface
from app.schemas.dashboard_dto import (
    FinancialSummaryResponse,
    MetricsSummary,
    OutstandingPaymentsResponse,
    PaginationInfo,
    OutstandingStatusFilter,
    OutstandingSummary,
    PeriodInfo,
)


class DashboardService:
    def __init__(self, repository: DashboardRepositoryInterface):
        self.repository = repository

    def _today(self) -> date:
        return date.today()

    def _resolve_limit(self, limit: Optional[int]) -> int:
        if limit is None:
            return 50
        return min(limit, 200)

    def _resolve_offset(self, offset: Optional[int]) -> int:
        if offset is None:
            return 0
        return offset

    def _parse_date(self, value: Optional[str]) -> Optional[date]:
        if value is None:
            return None

        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD",
            ) from exc

    def _apply_date_defaults(
        self,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> tuple[date, date]:
        today = self._today()
        resolved_start = start_date or today.replace(day=1)
        resolved_end = end_date or today
        return resolved_start, resolved_end

    def _validate_date_range(self, start_date: date, end_date: date) -> None:
        today = self._today()

        if end_date < start_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="end_date must be greater than or equal to start_date",
            )

        if end_date > today:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="end_date cannot be in the future",
            )

        if (end_date - start_date).days > 365:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Date range cannot exceed 1 year (365 days)",
            )

    def _get_last_day_of_month(self, value: date) -> date:
        return value.replace(day=monthrange(value.year, value.month)[1])

    def _format_month_day(self, value: date) -> str:
        return f"{value.strftime('%B')} {value.day}"

    def _generate_period_label(self, start_date: date, end_date: date) -> str:
        today = self._today()

        if start_date == today.replace(day=1) and end_date == today:
            return start_date.strftime("%B %Y (month-to-date)")

        if start_date.day == 1 and end_date == self._get_last_day_of_month(start_date):
            return start_date.strftime("%B %Y")

        if start_date.year == end_date.year:
            return f"{self._format_month_day(start_date)} – {self._format_month_day(end_date)}, {end_date.year}"

        return (
            f"{self._format_month_day(start_date)}, {start_date.year} – "
            f"{self._format_month_day(end_date)}, {end_date.year}"
        )

    async def get_financial_summary(
        self,
        business_id: UUID,
        user_id: Optional[UUID],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> FinancialSummaryResponse:
        del user_id  # TODO: replace with auth dependency

        parsed_start = self._parse_date(start_date)
        parsed_end = self._parse_date(end_date)
        resolved_start, resolved_end = self._apply_date_defaults(parsed_start, parsed_end)
        self._validate_date_range(resolved_start, resolved_end)

        if not await self.repository.business_exists(business_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found",
            )

        revenue = await self.repository.get_revenue(business_id, resolved_start, resolved_end)
        vat_liability = await self.repository.get_vat_liability(business_id, resolved_start, resolved_end)
        outstanding_receivables = await self.repository.get_outstanding_receivables(business_id)

        return FinancialSummaryResponse(
            business_id=business_id,
            period=PeriodInfo(
                start_date=resolved_start,
                end_date=resolved_end,
                label=self._generate_period_label(resolved_start, resolved_end),
            ),
            metrics=MetricsSummary(
                revenue=revenue,
                vat_liability=vat_liability,
                outstanding_receivables=outstanding_receivables,
            ),
        )

    async def get_outstanding_payments(
        self,
        business_id: UUID,
        user_id: Optional[UUID],
        status_filter: Optional[OutstandingStatusFilter] = None,
        customer_id: Optional[UUID] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> OutstandingPaymentsResponse:
        del user_id  # TODO: replace with auth dependency

        if not await self.repository.business_exists(business_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found",
            )

        resolved_limit = self._resolve_limit(limit)
        resolved_offset = self._resolve_offset(offset)

        invoices = await self.repository.get_outstanding_invoices(
            business_id=business_id,
            status=status_filter,
            customer_id=customer_id,
            limit=resolved_limit,
            offset=resolved_offset,
        )
        total_outstanding, total_invoices = await self.repository.get_outstanding_totals(
            business_id=business_id,
            status=status_filter,
            customer_id=customer_id,
        )

        return OutstandingPaymentsResponse(
            business_id=business_id,
            invoices=invoices,
            summary=OutstandingSummary(
                total_outstanding=total_outstanding,
                total_invoices=total_invoices,
            ),
            pagination=PaginationInfo(
                limit=resolved_limit,
                offset=resolved_offset,
                total=total_invoices,
            ),
        )
