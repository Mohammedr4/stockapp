#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Explicitly set the Django settings module
export DJANGO_SETTINGS_MODULE=project.settings

# Run Django database migrations
# This is often done before starting the server in a production environment
python manage.py migrate --noinput

# Run the Gunicorn web server
# The application will be served from project/wsgi.py
gunicorn project.wsgi --log-file - --bind 0.0.0.0:$PORT
