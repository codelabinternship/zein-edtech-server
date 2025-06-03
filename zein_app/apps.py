from django.apps import AppConfig
import os
import sys
import logging

logger = logging.getLogger(__name__)

class ZeinAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'zein_app'

    def ready(self):
        # Skip this during migrations or when DJANGO_SKIP_INIT_USERS is set
        if 'makemigrations' in sys.argv or 'migrate' in sys.argv:
            return

        # Wrap in try-except to avoid issues during initialization
        try:
            from django.contrib.auth import get_user_model
            from django.db import connection

            # Check if database is ready
            with connection.cursor() as cursor:
                try:
                    # Try to query the auth_user table
                    cursor.execute("SELECT COUNT(*) FROM auth_user")
                except Exception as e:
                    logger.warning(f"Database not ready: {str(e)}")
                    return

            User = get_user_model()

            # Auto-create dev user
            if not User.objects.filter(username='uzlance_0').exists():
                logger.info("Creating dev user...")
                User.objects.create_user(
                    username='uzlance_0',
                    password='Uzlance_0@',
                    full_name='Dev User',
                    role='dev'
                )
                logger.info("Dev user created successfully")

            # Auto-create super admin user
            if not User.objects.filter(username='super_admin').exists():
                logger.info("Creating super admin user...")
                User.objects.create_user(
                    username='super_admin',
                    password='super_admin',
                    full_name='Super Admin',
                    role='super_admin'
                )
                logger.info("Super admin user created successfully")

        except Exception as e:
            logger.error(f"Error creating default users: {str(e)}")
            # Don't silence the error completely
            raise
