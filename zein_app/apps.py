from django.apps import AppConfig
import os
import sys


class ZeinAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'zein_app'

    def ready(self):
        # Skip this during migrations or when DJANGO_SKIP_INIT_USERS is set
        if 'makemigrations' in sys.argv or 'migrate' in sys.argv or os.environ.get('DJANGO_SKIP_INIT_USERS'):
            return

        # Wrap in try-except to avoid issues during initialization
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()

            # Auto-create dev user
            if not User.objects.filter(username='uzlance_0').exists():
                User.objects.create_user(
                    username='uzlance_0',
                    password='Uzlance_0@',
                    full_name='Dev User',
                    role='dev'
                )
            # Auto-create super admin user
            if not User.objects.filter(username='super_admin').exists():
                User.objects.create_user(
                    username='super_admin',
                    password='super_admin',
                    full_name='Super Admin',
                    role='super_admin'
                )
        except Exception as e:
            # Silently pass during initialization errors
            pass
