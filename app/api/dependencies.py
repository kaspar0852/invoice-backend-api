from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.reminder_repository import ReminderRepository
from app.services.dashboard_service import DashboardService
from app.services.email_service import EmailService
from app.services.reminder_service import ReminderService


def get_dashboard_service(
    db: AsyncSession = Depends(get_db),
) -> DashboardService:
    return DashboardService(DashboardRepository(db))


def get_email_service() -> EmailService:
    return EmailService()


def get_reminder_service(
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
) -> ReminderService:
    return ReminderService(ReminderRepository(db), email_service)
