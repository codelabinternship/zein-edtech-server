from django.apps import AppConfig


class ZeinAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'zein_app'

    def ready(self):
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
