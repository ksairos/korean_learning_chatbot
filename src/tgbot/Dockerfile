FROM python:3.12-bookworm

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
ENV UV_COMPILE_BYTECODE=1

COPY pyproject.toml .
COPY uv.lock .
RUN pip install --no-cache-dir uv
RUN uv sync --frozen --only-group tgbot

COPY src/tgbot src/tgbot/
COPY src/config src/config/
COPY src/schemas src/schemas/
COPY data/ data/