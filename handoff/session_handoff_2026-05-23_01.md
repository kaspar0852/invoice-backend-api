# Handoff Document

## Project
- Repository: `/Users/kasper/inv-backend/invoice-backend-api`
- Stack: FastAPI, SQLAlchemy async, PostgreSQL, Alembic, Pydantic, pytest, Docker, `uv`
- Session type: implementation + debugging + developer tooling

## Session Summary
This session started with a full codebase analysis, including the Markdown docs and tests. After that, work focused on:

1. Adding a new invoice-side customer invoice API
2. Creating developer scripts for viewing and seeding realistic database data
3. Updating the README to document those scripts
4. Debugging runtime issues exposed by the new seeded data

## Existing Reference Artifacts
- General project overview: `/Users/kasper/inv-backend/invoice-backend-api/README.md`
- Product requirements: `/Users/kasper/inv-backend/invoice-backend-api/prd.md`
- Database design: `/Users/kasper/inv-backend/invoice-backend-api/tables.md`
- Slice planning: `/Users/kasper/inv-backend/invoice-backend-api/Proposed Vertical Slice Breakdown.md`
- Earlier analysis handoff: `/Users/kasper/inv-backend/invoice-backend-api/handoff/invoice-backend-analysis-handoff-2026-05-23.md`
- Prior generic handoff: `/Users/kasper/inv-backend/invoice-backend-api/handoff/session_handoff.md`

Use those as context instead of duplicating their contents.

## What Changed

### 1. Invoice-side customer invoice endpoint
- Added a new endpoint under the invoice module:
  - `GET /api/v1/invoices/customer/{customer_id}?business_id=...`
- Main files involved:
  - `/Users/kasper/inv-backend/invoice-backend-api/app/api/v1/routes/invoices_route.py`
  - `/Users/kasper/inv-backend/invoice-backend-api/app/services/invoice_service.py`
  - `/Users/kasper/inv-backend/invoice-backend-api/app/repositories/invoice_repository.py`
  - `/Users/kasper/inv-backend/invoice-backend-api/tests/test_invoices.py`

### 2. Data inspection script
- Added:
  - `/Users/kasper/inv-backend/invoice-backend-api/scripts/show_sample_data.sh`
- Purpose:
  - Print readable sample data across `users`, `businesses`, `user_businesses`, `customers`, `invoices`, `invoice_items`, and `payments`
  - Includes joined, business-friendly output and a business snapshot summary

### 3. Demo seed script
- Added:
  - `/Users/kasper/inv-backend/invoice-backend-api/scripts/seed_demo_data.sh`
- Purpose:
  - Seed realistic linked demo records across all main tables
  - Default behavior seeds `100` customers plus invoices, items, payments, users, memberships, and businesses
  - Intended for local dev/demo usage

### 4. README updates
- Updated:
  - `/Users/kasper/inv-backend/invoice-backend-api/README.md`
- Added documentation for:
  - `scripts/seed_demo_data.sh`
  - `scripts/show_sample_data.sh`
  - optional local workflow for seeding and inspecting demo data

## Important Runtime Issues Found During Session

### 1. Email validation mismatch in seeded data
- Original seed emails used a reserved/special-use domain like `@demo.local`
- `EmailStr` rejected those values during API response serialization
- Seed script was updated to use valid-looking domains such as `@seeded-demo.com`

### 2. SQLAlchemy enum mapping mismatch
- Database rows were storing enum values like `Sent`, `Paid`, `Owner`, and `Settled`
- ORM enum definitions were effectively reading member names instead of member values
- Models updated to use `values_callable=lambda enum_cls: [member.value for member in enum_cls]`
- Main files involved:
  - `/Users/kasper/inv-backend/invoice-backend-api/app/models/invoice.py`
  - `/Users/kasper/inv-backend/invoice-backend-api/app/models/payment.py`
  - `/Users/kasper/inv-backend/invoice-backend-api/app/models/user_business.py`

### 3. Customer DTO mismatch
- The customer transaction-history path was failing because `CustomerRead` expects:
  - `first_name`
  - `last_name`
  - `phone_number`
- The ORM model exposes:
  - `name`
  - `phone`
- The fix was to use the schema’s custom mapper path instead of direct model validation
- The user later said they fixed this themselves; verify final state in:
  - `/Users/kasper/inv-backend/invoice-backend-api/app/services/customer_service.py`

### 4. Repository interface mismatch
- `InvoiceRepositoryInterface` required `get_customer_invoices(...)`
- `InvoiceRepository` temporarily lacked the concrete implementation, causing instantiation failure
- This was fixed in:
  - `/Users/kasper/inv-backend/invoice-backend-api/app/repositories/invoice_repository.py`

## Validation Performed
- Full pytest run earlier in the session still showed customer test mismatches unrelated to the new scripts:
  - `14 passed, 2 failed`
  - failing area: customer GET tests expecting no `business_id`
- Invoice test subset passed after adding the new invoice-side endpoint:
  - `PYTHONPATH=. uv run pytest tests/test_invoices.py`
- OpenAPI generation succeeded and was written to:
  - `/Users/kasper/inv-backend/invoice-backend-api/openapi.generated.json`
- After enum/email fixes and reseeding, manual API sanity checks succeeded for:
  - `/api/v1/users/`
  - `/api/v1/customers/`
  - `/api/v1/invoices/`
  - `/api/v1/customers/{customer_id}/transactions?business_id=...`

## Useful Commands
- Run app:
  - `PYTHONPATH=. uv run uvicorn app.main:app --reload`
- Run all tests:
  - `PYTHONPATH=. uv run pytest`
- Seed demo data:
  - `./scripts/seed_demo_data.sh 100`
- View sample data:
  - `./scripts/show_sample_data.sh 15`

## Open Questions / Design Notes
1. There is currently API overlap between:
   - `/api/v1/customers/{customer_id}/invoices`
   - `/api/v1/invoices/customer/{customer_id}`
   These likely should not both survive long-term unless they intentionally serve different contracts.

2. Customer tests still appear out of sync with the current multi-tenant contract because some endpoints now require `business_id`.

3. The customer module still deserves a cleanup pass for consistency around DTO construction, tenant enforcement, and route ownership.

## Suggested Next Session Focus
1. Decide whether to keep both customer-side and invoice-side “get customer invoices” endpoints
2. Align customer tests with the intended API contract
3. Review customer module response mapping and tenant handling for consistency
4. Consider adding seed-data documentation or examples to Swagger/README if demo usage matters

## Suggested Skills
- Python/FastAPI backend development
- SQLAlchemy/PostgreSQL debugging
- API contract cleanup
- Test alignment and maintenance
- Project code analysis
