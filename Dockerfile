FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --no-install-project

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./

RUN uv sync --no-dev

EXPOSE 8000

CMD uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
