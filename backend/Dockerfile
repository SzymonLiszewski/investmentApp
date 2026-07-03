# Build context: backend/ (docker-compose uses context: ./backend)
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY . .

# Run as non-root user
# /models is the mountpoint for the shared trained-models volume; pre-create it
# owned by appuser so the named volume inherits writable ownership.
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app \
    && mkdir -p /models \
    && chown appuser:appuser /models
USER appuser

EXPOSE 8000

# Default: gunicorn (override in docker-compose.dev.yml with runserver)
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2"]
