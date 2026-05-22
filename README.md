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

