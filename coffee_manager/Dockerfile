FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock* ./

RUN python -m pip install --no-cache-dir "poetry>=2.0.0,<3.0.0" \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY src ./src

ENV PYTHONPATH=/app/src
EXPOSE 8000

CMD ["uvicorn", "coffee_manager.main:app", "--host", "0.0.0.0", "--port", "8000"]
