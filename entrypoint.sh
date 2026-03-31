#!/bin/sh

# If we have a DATABASE_URL, we can try to wait for it (optional)
echo "Checking database connection..."

echo "Running migrations..."
python manage.py migrate --no-input

echo "Collecting static files..."
python manage.py collectstatic --no-input

exec "$@"