#!/bin/bash
set -e

echo "Waiting for PostgreSQL to become ready..."
# Loop until we can connect to PostgreSQL (uses DATABASE_URL indirectly via psycopg2)
until python -c "
import psycopg2, os, re
url = os.environ.get('DATABASE_URL', '')
# Convert asyncpg URL to psycopg2-compatible URL
sync_url = re.sub(r'^postgresql\+asyncpg://', 'postgresql://', url)
conn = psycopg2.connect(sync_url)
conn.close()
print('PostgreSQL is ready.')
" 2>/dev/null; do
  echo "PostgreSQL is not ready yet. Retrying in 2 seconds..."
  sleep 2
done

echo "Running Alembic database migrations..."
alembic upgrade head

echo "Starting application..."
exec "$@"
