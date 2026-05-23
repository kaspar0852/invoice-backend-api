from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status

from app.repositories.reminder_repository import (
    ReminderInvoiceRecord,
    ReminderRepositoryInterface,
)
from app.schemas.reminder_dto import (
    ReminderSentItem,
    ReminderSkippedItem,
    SendRemindersRequest,
    SendRemindersResponse,
)
from app.services.email_service import EmailDeliveryError, EmailService


OUTSTANDING_STATUSES = {"Sent", "Partial", "Overdue"}


class ReminderService:
    def __init__(
        self,
        repository: ReminderRepositoryInterface,
        email_service: EmailService,
    ) -> None:
        self.repository = repository
        self.email_service = email_service

    def _today(self) -> date:
        return date.today()

    def _calculate_aging_days(self, due_date: date | None) -> int | None:
        if due_date is None:
            return None
        return (self._today() - due_date).days

    def _format_due_date(self, due_date: date | None) -> str:
        if due_date is None:
            return "Not specified"
        return due_date.strftime("%d %b %Y")

    def _render_subject(self, invoice: ReminderInvoiceRecord) -> str:
        return f"Payment reminder for invoice {invoice.invoice_number}"

    def _render_body(self, invoice: ReminderInvoiceRecord) -> str:
        due_date_text = self._format_due_date(invoice.due_date)
        lines = [
            f"Hello {invoice.customer_name},",
            "",
            f"This is a reminder from {invoice.business_name} about invoice {invoice.invoice_number}.",
            f"Total amount: {invoice.total_amount:.2f}",
            f"Remaining balance: {invoice.remaining_balance:.2f}",
            f"Due date: {due_date_text}",
        ]

        aging_days = self._calculate_aging_days(invoice.due_date)
        if invoice.status == "Overdue" and aging_days is not None and aging_days > 0:
            lines.append(f"This invoice is {aging_days} days overdue.")

        lines.extend(["", "Please arrange payment at your earliest convenience."])
        return "\n".join(lines)

    async def send_reminders(
        self,
        request: SendRemindersRequest,
        user_id: Optional[UUID],
    ) -> SendRemindersResponse:
        del user_id  # TODO: replace with auth dependency

        if not await self.repository.business_exists(request.business_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found",
            )

        invoices = await self.repository.get_invoices_for_reminder(
            business_id=request.business_id,
            invoice_ids=request.invoice_ids,
        )
        invoice_map = {invoice.invoice_id: invoice for invoice in invoices}

        sent: list[ReminderSentItem] = []
        skipped: list[ReminderSkippedItem] = []

        for invoice_id in request.invoice_ids:
            invoice = invoice_map.get(invoice_id)
            if invoice is None:
                skipped.append(
                    ReminderSkippedItem(
                        invoice_id=invoice_id,
                        reason="Invoice not found or does not belong to this business",
                    )
                )
                continue

            if invoice.status not in OUTSTANDING_STATUSES:
                skipped.append(
                    ReminderSkippedItem(
                        invoice_id=invoice_id,
                        reason=f"Invoice status is not outstanding (status: {invoice.status})",
                    )
                )
                continue

            if invoice.customer_email is None or not invoice.customer_email.strip():
                skipped.append(
                    ReminderSkippedItem(
                        invoice_id=invoice_id,
                        reason="No email on file for this customer",
                    )
                )
                continue

            subject = self._render_subject(invoice)
            body = self._render_body(invoice)

            try:
                self.email_service.send(invoice.customer_email, subject, body)
            except EmailDeliveryError as exc:
                await self.repository.log_reminder(
                    invoice_id=invoice.invoice_id,
                    business_id=request.business_id,
                    recipient_email=invoice.customer_email,
                    channel="email",
                    status="failed",
                    error_message=str(exc),
                )
                skipped.append(
                    ReminderSkippedItem(
                        invoice_id=invoice_id,
                        reason=str(exc),
                    )
                )
                continue

            await self.repository.log_reminder(
                invoice_id=invoice.invoice_id,
                business_id=request.business_id,
                recipient_email=invoice.customer_email,
                channel="email",
                status="sent",
                error_message=None,
            )
            sent.append(
                ReminderSentItem(
                    invoice_id=invoice.invoice_id,
                    recipient_email=invoice.customer_email,
                    customer_name=invoice.customer_name,
                )
            )

        return SendRemindersResponse(sent=sent, skipped=skipped)
