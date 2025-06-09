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

# Copy start.sh script and give execution permission
COPY start.sh .
RUN chmod +x start.sh

# Set Django settings module to production settings
ENV DJANGO_SETTINGS_MODULE=zeinedtech.settings_prod
ENV DJANGO_SKIP_INIT_USERS=1

# Create staticfiles directory
RUN mkdir -p staticfiles

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Start backend + bot via shell script
CMD ["./start.sh"]
