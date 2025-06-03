from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates default users for the application'

    def handle(self, *args, **kwargs):
        # Create dev user
        if not User.objects.filter(username='uzlance_0').exists():
            self.stdout.write('Creating dev user...')
            User.objects.create_user(
                username='uzlance_0',
                password='Uzlance_0@',
                full_name='Dev User',
                role='dev'
            )
            self.stdout.write(self.style.SUCCESS('Dev user created successfully'))

        # Create super admin user
        if not User.objects.filter(username='super_admin').exists():
            self.stdout.write('Creating super admin user...')
            User.objects.create_user(
                username='super_admin',
                password='super_admin',
                full_name='Super Admin',
                role='super_admin'
            )
            self.stdout.write(self.style.SUCCESS('Super admin user created successfully'))

        self.stdout.write(self.style.SUCCESS('All default users have been created'))
