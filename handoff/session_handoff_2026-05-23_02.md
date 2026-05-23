# Handoff Document

## Project
- Repository: `/Users/kasper/inv-backend/invoice-backend-api`
- Stack: FastAPI, SQLAlchemy async, PostgreSQL, Alembic, Pydantic, pytest, Docker, `uv`
- Session type: feature implementation + testing

## Session Summary
This session implemented the financial summary dashboard feature end to end, including DTOs, repository queries, service orchestration, route wiring, and automated tests.

## Primary Feature Delivered
### Financial Summary Dashboard
- Added endpoint:
  - `GET /api/v1/dashboard/financial-summary`
- Registered router under:
  - `/api/v1/dashboard`

### Implemented behavior
- Required query param:
  - `business_id`
- Optional query params:
  - `start_date`
  - `end_date`
- Date parsing now uses custom service parsing so malformed dates return:
  - `"Invalid date format. Use YYYY-MM-DD"`
- Date defaulting:
  - `start_date`: first day of current month when omitted
  - `end_date`: today when omitted
- Date validation errors implemented with exact PRD messages:
  - `"end_date must be greater than or equal to start_date"`
  - `"end_date cannot be in the future"`
  - `"Date range cannot exceed 1 year (365 days)"`
- Period label generation implemented for:
  - month-to-date
  - full-month
  - custom range
- Unknown `business_id` returns:
  - `404 Business not found`

## Files Added
- `/Users/kasper/inv-backend/invoice-backend-api/app/schemas/dashboard_dto.py`
- `/Users/kasper/inv-backend/invoice-backend-api/app/repositories/dashboard_repository.py`
- `/Users/kasper/inv-backend/invoice-backend-api/app/services/dashboard_service.py`
- `/Users/kasper/inv-backend/invoice-backend-api/app/api/dependencies.py`
- `/Users/kasper/inv-backend/invoice-backend-api/app/api/v1/routes/dashboard_route.py`
- `/Users/kasper/inv-backend/invoice-backend-api/tests/test_dashboard.py`

## Files Updated
- `/Users/kasper/inv-backend/invoice-backend-api/app/api/v1/__init__.py`
- `/Users/kasper/inv-backend/invoice-backend-api/app/api/v1/routes/__init__.py`
- `/Users/kasper/inv-backend/invoice-backend-api/app/services/__init__.py`
- `/Users/kasper/inv-backend/invoice-backend-api/pyproject.toml`
- `/Users/kasper/inv-backend/invoice-backend-api/uv.lock`

## DTO Layer
- Added:
  - `FinancialSummaryResponse`
  - `PeriodInfo`
  - `MetricsSummary`
- Monetary fields use `Decimal`
- Monetary values are normalized to 2 decimal places with `ROUND_HALF_UP`
- JSON serialization currently emits numeric JSON values for the metrics

## Repository Layer
Added `DashboardRepository` with:
- `business_exists(business_id)`
- `get_revenue(business_id, start_date, end_date)`
- `get_vat_liability(business_id, start_date, end_date)`
- `get_outstanding_receivables(business_id)`

### Repository behavior implemented
- Revenue:
  - sums only `Settled` payments
  - applies date range filter
  - isolates by `business_id`
  - returns `0.00` when empty
- VAT liability:
  - joins payments to invoices
  - calculates proportional VAT using payment amount against invoice VAT/total
  - skips invoices with `total_amount = 0`
  - returns `0.00` when empty
- Outstanding receivables:
  - includes only `Sent`, `Partial`, `Overdue`
  - deducts only `Settled` payments
  - ignores `Draft`, `Paid`, and `Cancelled`
  - has no date filter

## Service Layer
Added `DashboardService` with:
- `_parse_date`
- `_apply_date_defaults`
- `_validate_date_range`
- `_generate_period_label`
- `_get_last_day_of_month`
- `get_financial_summary`

## Route / Dependency Wiring
- Added `get_dashboard_service` in:
  - `/Users/kasper/inv-backend/invoice-backend-api/app/api/dependencies.py`
- Added route in:
  - `/Users/kasper/inv-backend/invoice-backend-api/app/api/v1/routes/dashboard_route.py`
- The route currently passes:
  - `user_id=None`
- Auth placeholder comment added:
  - `# TODO: replace with auth dependency`

## Testing Added
### Dashboard tests
`/Users/kasper/inv-backend/invoice-backend-api/tests/test_dashboard.py`

Coverage includes:
- DTO rounding and serialization
- Repository aggregate queries against a real async SQLite test database
- Multi-tenant isolation across two businesses
- Partial payments
- Zero-total invoice handling
- Empty-period results
- Service defaulting, validation, and period label generation
- HTTP happy path
- HTTP error responses
- OpenAPI route presence

## Validation Performed
- Ran:
  - `PYTHONPATH=. uv run pytest -q tests/test_dashboard.py`
- Result:
  - `16 passed`

- Ran:
  - `PYTHONPATH=. uv run pytest -q`
- Result:
  - `32 passed`

## Important Notes
1. The route accepts `start_date` and `end_date` as strings intentionally, not `date` query params, so the app can return the exact PRD-required malformed-date message instead of FastAPI’s default validation payload.
2. The dashboard service currently performs only business existence checking, not user-to-business authorization.
3. `aiosqlite` was added to the dev dependency group so repository tests can run against an in-memory async database.

## Related Prior Session State
There were already uncommitted changes in the worktree before this session, including:
- invoice-side customer invoice endpoint work
- customer test alignment

Those were not reverted. The dashboard changes were added on top of the existing worktree state.

## Suggested Next Session Focus
1. Add business-authorization enforcement once the auth dependency is available
2. Decide whether the dashboard route should use parallel query execution in the service for performance
3. Consider adding database indexes from the PRD if dashboard query volume grows
4. If needed, document the dashboard endpoint in `README.md`

## No Commit Status
- No commit was created in this session
- Changes remain in the working tree
