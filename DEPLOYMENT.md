# Deployment Guide

## Docker (recommended)

1. Copy environment template and adjust values:

```bash
cp .env.example .env
```

2. Build and run the stack (Django + Postgres + Redis + Celery + Bot):

```bash
docker compose up -d --build
```

This will start:
- web: Django served by Gunicorn on port 8000
- db: Postgres 15
- redis: Redis 7 (Celery broker/result backend)
- celeryworker: Celery worker
- celerybeat: Celery beat scheduler
- bot: Telegram bot in polling mode (set TELEGRAM_MODE=webhook to use webhooks instead)

Open the API docs at http://localhost:8000/api/docs/

To stop the stack:

```bash
docker compose down
```

## Production notes

- Set DEBUG=False and a strong SECRET_KEY in your .env
- Set ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS appropriately
- Set TELEGRAM_MODE=webhook and TELEGRAM_WEBHOOK_URL to your HTTPS URL if deploying the bot via webhooks
- Optionally put Nginx in front of the web service and terminate TLS there
- Static files are served by WhiteNoise; collectstatic runs automatically on container start
