FROM python:3.12-bookworm

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
ENV UV_COMPILE_BYTECODE=1

COPY pyproject.toml .
COPY uv.lock .
RUN pip install --no-cache-dir uv
RUN uv sync --frozen --no-install-project --no-dev

COPY src/api src/api/
COPY src/config src/config/
COPY src/schemas src/schemas/
COPY src/llm_agent src/llm_agent/
COPY data/ data/