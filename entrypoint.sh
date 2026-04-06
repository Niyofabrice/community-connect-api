#!/bin/sh

echo "Checking database connection..."

echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate --no-input

echo "Collecting static files..."
python manage.py collectstatic --no-input

celery -A core worker -l info

exec "$@"