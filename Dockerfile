# Dockerfile for back_elvet Django app
FROM python:3.12.3-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first (leverage Docker cache)
COPY requirements.prod.txt /app/
# Upgrade pip tooling first; ensure we can build wheels if necessary (psycopg2)
RUN pip install --upgrade pip setuptools wheel && pip install -r requirements.prod.txt

# Copy project
COPY . /app

# Create non-root user
RUN chmod +x /app/entrypoint.sh && useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Entrypoint handles migrations, collectstatic, then starts gunicorn
ENTRYPOINT ["/app/entrypoint.sh"]
