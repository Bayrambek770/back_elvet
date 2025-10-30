# Dockerfile for back_elvet Django app
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first (leverage Docker cache)
COPY requirements.prod.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.prod.txt

# Copy project
COPY . /app

# Create non-root user
RUN chmod +x /app/entrypoint.sh && useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Entrypoint handles migrations, collectstatic, then starts gunicorn
ENTRYPOINT ["/app/entrypoint.sh"]
