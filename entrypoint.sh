#!/usr/bin/env bash
set -euo pipefail

# Wait for Postgres if DATABASE_URL points to it
if [[ -n "${DATABASE_URL:-}" ]]; then
  if [[ "$DATABASE_URL" == postgres* ]]; then
    echo "Waiting for Postgres to be available..."
    host=$(python - <<'PY'
import os
from urllib.parse import urlparse
url = os.environ.get('DATABASE_URL')
parts = urlparse(url)
print(parts.hostname or 'localhost')
PY
)
    port=$(python - <<'PY'
import os
from urllib.parse import urlparse
url = os.environ.get('DATABASE_URL')
parts = urlparse(url)
print(parts.port or 5432)
PY
)
    until nc -z "$host" "$port"; do
      >&2 echo "Postgres is unavailable - sleeping"
      sleep 1
    done
    echo "Postgres is up"
  fi
fi

python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Start gunicorn
exec gunicorn -c gunicorn.conf.py config.wsgi:application
