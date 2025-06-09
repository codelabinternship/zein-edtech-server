# Quiz Bot Application

A Django application with a Telegram bot.

## Development Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 15+
- Docker and Docker Compose (optional, for containerized setup)

### Local Setup

1. Clone the repository:
   ```
   git clone <repository_url>
   cd quiz_application_backend
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file:
   ```
   # Django settings
   DEBUG=True
   SECRET_KEY=django-insecure-mj6g9t0h$6@o-u813a=f0&%lb9-p(^u1%yk0@3fxl+qj46+$af
   DJANGO_SETTINGS_MODULE=zeinedtech.settings
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

   # Database settings for PostgreSQL
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=clonezein
   DB_USER=postgres
   DB_PASSWORD=root
   DB_HOST=localhost
   DB_PORT=5432

   # PostgreSQL for Docker Compose
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=root
   POSTGRES_DB=clonezein

   # Telegram Bot
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   ```

5. Run migrations:
   ```
   python manage.py migrate
   ```

6. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

7. Run the server:
   ```
   python manage.py runserver
   ```

8. In a separate terminal, run the Telegram bot:
   ```
   python manage.py run_bot
   ```

### Docker Setup

1. Make sure Docker and Docker Compose are installed.
2. Create a `.env` file as described above but change DB_HOST to `db`.
3. Run Docker Compose:
   ```
   docker-compose up -d
   ```

## Deployment on Render

### Prerequisites

- A Render account (https://render.com)
- A Telegram bot token from BotFather

### Deployment Steps

1. Push your code to a Git repository (GitHub, GitLab, etc.).

2. Login to Render and create a new "Blueprint" instance.

3. Connect your Git repository and Render will automatically detect the `render.yaml` file.

4. Set the required environment variables:
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token

5. Click "Apply" and Render will create:
   - A PostgreSQL database
   - A web service for the Django application
   - A worker service for the Telegram bot

6. Once deployed, you can access your application at the URL provided by Render.

### Manual Deployment (Alternative)

If you prefer not to use the Blueprint:

1. Create a PostgreSQL database in Render.

2. Create a Web Service:
   - Connect to your repository
   - Set the build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - Set the start command: `gunicorn zeinedtech.wsgi:application --bind 0.0.0.0:$PORT`
   - Set environment variables:
     - `DJANGO_SETTINGS_MODULE=zeinedtech.settings_prod`
     - `DEBUG=False`
     - `SECRET_KEY` (generate a random secure key)
     - `DJANGO_ALLOWED_HOSTS=.onrender.com,your-app-name.onrender.com`
     - `DATABASE_URL` (from your PostgreSQL instance)
     - `TELEGRAM_BOT_TOKEN`

3. Create a Background Worker:
   - Connect to the same repository
   - Set the build command: `pip install -r requirements.txt`
   - Set the start command: `python manage.py run_bot`
   - Use the same environment variables as the web service

4. Deploy both the web service and worker.

## Files for Deployment

- `Dockerfile`: Defines the container image
- `docker-compose.yml`: For local development with Docker
- `.dockerignore`: Excludes unnecessary files from Docker build
- `render.yaml`: Configuration for Render deployment
- `zeinedtech/settings_prod.py`: Production settings
# zein-edtech-server
# zein-server-v2
