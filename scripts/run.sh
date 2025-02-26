#!/bin/sh

set -e

# Wait for DB to be ready
python manage.py wait_for_db

# Run database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start the uWSGI server (use this in production)
uwsgi --socket :9000 --workers 4 --master --enable-threads --module app.wsgi