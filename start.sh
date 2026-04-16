#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "Waiting for PostgreSQL..."
  sleep 1
done
echo "PostgreSQL is ready."

if [ "$ENVIRONMENT" = "production" ]; then
    echo "Starting production server..."
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput
    exec gunicorn --bind :${PORT:-8000} --workers 4 --threads 2 --timeout 60 \
        --access-logfile - --error-logfile - --log-level info \
        backend.wsgi:application
else
    echo "Starting development server..."
    python manage.py migrate
    exec python manage.py runserver 0.0.0.0:8000
fi
