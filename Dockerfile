# Use official uv image for caching and copying the binary
FROM ghcr.io/astral-sh/uv:0.11.15 AS uv_image

# Runtime stage
FROM python:3.12-slim AS runtime

# Copy uv from the installer
COPY --from=uv_image /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Prevent python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevent python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1
# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
# Prevent uv from using system dependencies
ENV UV_LINK_MODE=copy

# Mount cache for faster rebuilds, install dependencies first
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Copy the rest of the application
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini alembic.ini
COPY .env.example .env.example

# Sync the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose port and run the app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
