FROM python:3.12-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

COPY pyproject.toml ./
COPY src ./src

RUN pip install --no-cache-dir \
    'aiogram>=3.15,<4' \
    'httpx>=0.27' \
    'pydantic>=2.9' \
    'pydantic-settings>=2.5'

WORKDIR /app/src
CMD ["python", "main.py"]
