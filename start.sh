#!/bin/bash

echo "🎯 Collecting static files..."
python manage.py collectstatic --noinput

echo "🚀 Starting Telegram bot in background..."
python manage.py run_bot &

echo "🌐 Starting Gunicorn server..."
exec gunicorn zeinedtech.wsgi:application --bind 0.0.0.0:${PORT:-8000}
