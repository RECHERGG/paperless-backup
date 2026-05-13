FROM python:3.14-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project


FROM python:3.14-slim

WORKDIR /app

COPY --from=docker:cli /usr/local/bin/docker /usr/local/bin/docker

COPY --from=builder /app/.venv /app/.venv

COPY app/ ./app/
COPY main.py config.toml ./

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

ENTRYPOINT ["python", "main.py"]