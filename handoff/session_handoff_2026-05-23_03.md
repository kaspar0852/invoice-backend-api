# Handoff Document

## Project
- Repository: `/Users/kasper/inv-backend/invoice-backend-api`
- Stack: FastAPI, SQLAlchemy async, PostgreSQL, Alembic, Pydantic, pytest, Docker, `uv`
- Session type: feature implementation + migration + testing

## Session Summary
This session implemented Story 4.2, Automated Payment Reminders, end to end. The work included DTOs, reminder log persistence, SMTP delivery abstraction, repository and service layers, route wiring, migration work, and test coverage.

## Feature Delivered
### Automated Payment Reminders
- Added endpoint:
  - `POST /api/v1/dashboard/reminders`

### Implemented behavior
- Request body:
  - `business_id`
  - `invoice_ids`
- `invoice_ids` enforces minimum length `1`
- Unknown business returns:
  - `404 Business not found`
- Valid requests always return `200` with:
  - `sent`
  - `skipped`
- Skip reasons implemented:
  - `"Invoice not found or does not belong to this business"`
  - `"Invoice status is not outstanding (status: X)"`
  - `"No email on file for this customer"`
  - SMTP failure message from `EmailDeliveryError`
- Eligible invoices:
  - send plain-text email
  - log reminder row with `status='sent'`
- SMTP failures:
  - log reminder row with `status='failed'`
  - continue processing remaining invoices
- Remaining balance is calculated using settled payments only
- Null due date renders:
  - `"Not specified"`

## Files Added
- `/Users/kasper/inv-backend/invoice-backend-api/app/schemas/reminder_dto.py`
- `/Users/kasper/inv-backend/invoice-backend-api/app/models/reminder_log.py`
- `/Users/kasper/inv-backend/invoice-backend-api/app/repositories/reminder_repository.py`
- `/Users/kasper/inv-backend/invoice-backend-api/app/services/email_service.py`
- `/Users/kasper/inv-backend/invoice-backend-api/app/services/reminder_service.py`
- `/Users/kasper/inv-backend/invoice-backend-api/alembic/versions/c4d5e6f7a8b9_add_reminder_logs.py`
- `/Users/kasper/inv-backend/invoice-backend-api/tests/test_reminders.py`
- `/Users/kasper/inv-backend/invoice-backend-api/handdown/session_handoff_2026-05-23_03.md`

## Files Updated
- `/Users/kasper/inv-backend/invoice-backend-api/app/core/config.py`
- `/Users/kasper/inv-backend/invoice-backend-api/app/models/__init__.py`
- `/Users/kasper/inv-backend/invoice-backend-api/app/api/dependencies.py`
- `/Users/kasper/inv-backend/invoice-backend-api/app/api/v1/routes/dashboard_route.py`
- `/Users/kasper/inv-backend/invoice-backend-api/app/services/__init__.py`

## DTO Layer
Added:
- `SendRemindersRequest`
- `ReminderSentItem`
- `ReminderSkippedItem`
- `SendRemindersResponse`

Notes:
- `invoice_ids` uses `min_length=1`
- No business logic was added to the DTO layer

## Migration / Schema Work
Added Alembic migration:
- `/Users/kasper/inv-backend/invoice-backend-api/alembic/versions/c4d5e6f7a8b9_add_reminder_logs.py`

Table added:
- `reminder_logs`

Columns:
- `Id`
- `InvoiceId`
- `BusinessId`
- `RecipientEmail`
- `Channel`
- `SentAt`
- `Status`
- `ErrorMessage`

Constraints:
- FK to `invoices.Id`
- FK to `businesses.Id`

## Email Service
Added:
- `EmailService`
- `EmailDeliveryError`

Environment-backed config fields added in `app/core/config.py`:
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM_NAME`

Current behavior:
- Uses Gmail-compatible SMTP flow
- Sends plain-text email only
- Sets display name in `From`
- Wraps SMTP failures in `EmailDeliveryError`

## Reminder Repository
Added repository methods:
- `business_exists`
- `get_invoices_for_reminder`
- `log_reminder`

Repository behavior:
- Fetches only invoices for the requested `business_id`
- Joins invoice to customer and business data
- Calculates `remaining_balance` from settled payments only
- Missing invoice IDs are silently absent from results
- `log_reminder` is append-only and supports both `sent` and `failed`

## Reminder Service
Added `ReminderService.send_reminders`.

Key behavior:
1. Checks business existence
2. Fetches invoice/customer data for provided IDs
3. Skips missing invoices
4. Skips non-outstanding statuses
5. Skips customers with missing email
6. Renders subject/body
7. Sends via `EmailService`
8. Logs `sent` or `failed`
9. Returns aggregated `sent` and `skipped` response

Template details:
- Subject:
  - `Payment reminder for invoice <invoice_number>`
- Body includes:
  - business name
  - customer name
  - invoice number
  - total amount
  - remaining balance
  - due date
- Overdue invoices include overdue day count in body

## Route / Dependency Wiring
Updated:
- `/Users/kasper/inv-backend/invoice-backend-api/app/api/dependencies.py`
- `/Users/kasper/inv-backend/invoice-backend-api/app/api/v1/routes/dashboard_route.py`

Added dependency helpers:
- `get_email_service`
- `get_reminder_service`

The route currently passes:
- `user_id=None`

Auth placeholder remains:
- `# TODO: replace with auth dependency`

## Testing Added
### Reminder tests
`/Users/kasper/inv-backend/invoice-backend-api/tests/test_reminders.py`

Coverage includes:
- DTO validation and serialization
- SMTP send behavior with mocked SMTP
- SMTP error wrapping
- Repository invoice fetch behavior
- Repository reminder log persistence
- Service success, skip, mixed-batch, and SMTP failure flows
- Null due date template rendering
- HTTP route happy path
- HTTP route all-skipped path
- HTTP route mixed sent/skipped path
- HTTP validation errors
- HTTP unknown business path
- OpenAPI route presence

## Validation Performed
- Ran:
  - `PYTHONPATH=. uv run pytest -q tests/test_reminders.py`
- Result:
  - `17 passed`

- Ran:
  - `PYTHONPATH=. uv run pytest -q tests/test_reminders.py tests/test_dashboard.py`
- Result:
  - `42 passed`

- Ran:
  - `PYTHONPATH=. uv run pytest -q`
- Result:
  - `58 passed`

- Ran migration verification against a temporary SQLite database:
  - `alembic upgrade head`
  - `alembic downgrade -1`
- Result:
  - both succeeded

## Important Notes
1. The email service currently uses synchronous `smtplib` inside the request flow. It is testable and correct for this slice, but it is not background-job based yet.
2. The reminder route lives under the existing dashboard router alongside:
  - financial summary
  - outstanding payments
3. Reminder sending currently supports only the `email` channel, but the service boundary was kept small enough for future SMS or WhatsApp siblings.

## Related Prior Session State
This session built on earlier uncommitted work already present in the tree, including:
- financial summary dashboard
- outstanding payments dashboard
- earlier invoice/customer changes

Those prior changes were not reverted.

## Suggested Next Session Focus
1. Add README documentation for the reminders endpoint and required SMTP env vars
2. Consider moving reminder delivery to a background task or job queue if request latency becomes an issue
3. Add richer email templating or HTML delivery if product scope expands
4. Add authorization checks once the auth dependency is available

## No Commit Status
- No commit was created in this session
- Changes remain in the working tree
