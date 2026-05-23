# Invoice System API

A professional, production-ready FastAPI backend project featuring an N-Tier layered architecture, managed with `uv`, containerized with Docker, and integrated with SQLAlchemy 2.0 (asyncpg) + Alembic.

---

## 🛠️ Stack & Technologies
* **Framework:** FastAPI
* **Database:** PostgreSQL
* **ORM:** SQLAlchemy 2.x (async compatible using `asyncpg`)
* **Migrations:** Alembic
* **Package Manager:** `uv` (for lightning-fast Python dependency management)
* **Containerization:** Docker & Docker Compose
* **Testing:** Pytest (using `pytest-asyncio` for async tests)

---

## 🏛️ Architecture (N-Tier)
The codebase enforces strict separation of concerns across these layers:
1. **API Layer (`app/api`)** — Handles route definitions, request/response models serialization via Pydantic, CORS, and standard HTTP concerns.
2. **Service Layer (`app/services`)** — House for business logic, validations, orchestration, password hashing, and domain exceptions.
3. **Repository Layer (`app/repositories`)** — Direct data access layer. Exposes interface classes (`UserRepositoryInterface`) and concrete SQLAlchemy implementations encapsulating all SQL queries and ORM calls.
4. **Model Layer (`app/models`)** — Contains SQLAlchemy declarative mapping schemas (source of truth for database layout).
5. **Schema Layer (`app/schemas`)** — Houses Pydantic DTOs for type validation and response parsing.

---

## 📂 Project Layout
```
project-root/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── routes/          # API route definitions
│   ├── core/
│   │   ├── config.py            # Settings parsing via Pydantic Settings v2
│   │   ├── database.py          # SQLAlchemy engine, session maker, Base
│   │   └── dependencies.py      # Shared dependencies (e.g. get_db)
│   ├── models/                  # SQLAlchemy ORM models
│   ├── schemas/                 # Pydantic DTO schemas
│   ├── services/                # Business logic layer
│   ├── repositories/            # Data access layer
│   └── main.py                  # App entry point and factory
├── alembic/
│   ├── versions/
│   └── env.py                   # Async-configured migrations environment
├── scripts/
│   ├── seed_demo_data.sh        # Seed realistic demo data
│   └── show_sample_data.sh      # Inspect sample rows from all main tables
├── tests/
│   └── ...                      # Healthcheck and mocked route tests
├── .env.example
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml               # uv-managed packaging configuration
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
* [Docker](https://www.docker.com/) & Docker Compose
* Alternatively, Python 3.12+ and [uv](https://github.com/astral-sh/uv) installed locally.

---

### Local Setup (Without Docker)

1. **Clone & Install Dependencies:**
   ```bash
   uv sync
   ```

2. **Configure Environment:**
   ```bash
   cp .env.example .env
   ```
   *Make sure to configure database variables to point to a running local PostgreSQL instance.*

3. **Run Migrations:**
   ```bash
   uv run alembic upgrade head
   ```

4. **Start Application:**
   ```bash
   PYTHONPATH=. uv run uvicorn app.main:app --reload
   ```
   *Open [http://localhost:8000/docs](http://localhost:8000/docs) to browse Swagger UI documentation.*

5. **Optional: Seed Realistic Demo Data**
   ```bash
   ./scripts/seed_demo_data.sh
   ```
   *Seeds linked demo records for businesses, users, memberships, customers, invoices, invoice items, and payments.*

6. **Optional: Inspect Sample Data**
   ```bash
   ./scripts/show_sample_data.sh 15
   ```
   *Prints readable sample rows from the main tables using joined, business-friendly views.*

---

### Docker setup (Recommended)

To build and spin up the complete stack (Postgres + API application):

```bash
docker compose up --build
```

* This spins up PostgreSQL (`db` service) and runs a healthcheck on it.
* Once the database is healthy, it builds the multi-stage FastAPI container (`api` service) and starts it on port `8000`.
* The postgres data is persisted in a named volume (`postgres_data`).

---

## 🧪 Testing

To run the test suite (uses `pytest` and `pytest-asyncio` with mocked database interactions):


```bash
PYTHONPATH=. uv run pytest
```

---

## 📌 Implemented API Surface

The repository currently includes these business-facing API areas under `/api/v1`:

* `customers`
  * `GET /customers/{customer_id}?business_id=...`
  * `GET /customers/{customer_id}/invoices?business_id=...`
  * `GET /customers/{customer_id}/payments?business_id=...`
  * `GET /customers/{customer_id}/balance?business_id=...`
  * `GET /customers/{customer_id}/transactions?business_id=...`
* `invoices`
  * `GET /invoices/`
  * `GET /invoices/customer/{customer_id}?business_id=...`
* `dashboard`
  * `GET /dashboard/financial-summary?business_id=...`
  * `GET /dashboard/outstanding-payments?business_id=...`
  * `POST /dashboard/reminders`

OpenAPI docs are available at `/docs` when the app is running locally.

---

## 📊 Dashboard Endpoints

### Financial Summary

```http
GET /api/v1/dashboard/financial-summary?business_id=<uuid>&start_date=2026-05-01&end_date=2026-05-23
```

Behavior:
* `business_id` is required for tenant isolation.
* `start_date` and `end_date` are optional and must use `YYYY-MM-DD`.
* When omitted, the period defaults to the first day of the current month through today.
* Validation errors return custom messages such as `Invalid date format. Use YYYY-MM-DD` and `end_date cannot be in the future`.

Response shape:
* `business_id`
* `period`
* `metrics.revenue`
* `metrics.vat_liability`
* `metrics.outstanding_receivables`

### Outstanding Payments

```http
GET /api/v1/dashboard/outstanding-payments?business_id=<uuid>&status=Overdue&limit=25&offset=0
```

Optional filters:
* `status`: `Sent`, `Partial`, or `Overdue`
* `customer_id`
* `limit` and `offset`

Response shape:
* `business_id`
* `invoices[]` with invoice, customer, aging, and remaining balance fields
* `summary.total_outstanding`
* `summary.total_invoices`
* `pagination.limit`
* `pagination.offset`
* `pagination.total`

### Send Payment Reminders

```http
POST /api/v1/dashboard/reminders
Content-Type: application/json

{
  "business_id": "<uuid>",
  "invoice_ids": ["<invoice-uuid>"]
}
```

Behavior:
* Sends plain-text email reminders for eligible outstanding invoices.
* Returns both `sent` and `skipped` arrays so batch requests can partially succeed.
* Skip reasons include missing invoices, non-outstanding statuses, missing customer email, and SMTP delivery failures.
* Reminder delivery and logging are synchronous in the current slice.

---

## ✉️ SMTP Configuration

Reminder emails require the SMTP settings in `.env`:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_NAME="Invoice System"
```

Notes:
* `SMTP_FROM_NAME` should be a display name only, not a full `"Name <email>"` value.
* If SMTP settings are incomplete, reminder requests will skip delivery with an SMTP configuration error.

## 🧰 Demo Data Scripts

The repository includes two shell utilities for local development:

1. **Seed realistic demo data**
   ```bash
   ./scripts/seed_demo_data.sh
   ```
   *Default behavior seeds `100` customers, `100` invoices, `200` invoice items, and matching payment records.*

   You can pass a custom customer count:
   ```bash
   ./scripts/seed_demo_data.sh 250
   ```

2. **View readable sample data**
   ```bash
   ./scripts/show_sample_data.sh
   ```
   *Shows data from `users`, `businesses`, `user_businesses`, `customers`, `invoices`, `invoice_items`, and `payments` in a readable format.*

   You can pass a custom row limit from `1` to `15`:
   ```bash
   ./scripts/show_sample_data.sh 15
   ```

Both scripts read `.env` first and fall back to `.env.example` if needed.
