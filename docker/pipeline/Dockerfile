FROM python:3.11-slim

WORKDIR /app

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project metadata and install dependencies
COPY pyproject.toml ./
RUN uv pip install --system -e ".[dev]"

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Ensure PATH has the entry point
ENV PYTHONPATH=/app/src

# Default command (overridden in docker-compose)
CMD ["tushare-db", "scheduler-run"]
