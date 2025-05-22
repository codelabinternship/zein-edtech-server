FROM python:3.12-slim

WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  gcc \
  postgresql-client \
  libpq-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Set Django settings module to production settings
ENV DJANGO_SETTINGS_MODULE=bot_zein.settings_prod
ENV DJANGO_SKIP_INIT_USERS=1

# Create staticfiles directory
RUN mkdir -p staticfiles

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Run gunicorn
CMD gunicorn bot_zein.wsgi:application --bind 0.0.0.0:$PORT
