#!/bin/sh
set -e

python - <<'PY'
import os
import time

import psycopg

if not os.environ.get("POSTGRES_DB"):
    raise SystemExit

dsn = {
    "dbname": os.environ["POSTGRES_DB"],
    "user": os.environ["POSTGRES_USER"],
    "password": os.environ["POSTGRES_PASSWORD"],
    "host": os.environ.get("POSTGRES_HOST", "db"),
    "port": os.environ.get("POSTGRES_PORT", "5432"),
}

for attempt in range(60):
    try:
        with psycopg.connect(**dsn):
            break
    except psycopg.OperationalError:
        if attempt == 59:
            raise
        time.sleep(1)
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
