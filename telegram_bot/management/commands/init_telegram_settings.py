from django.core.management.base import BaseCommand
from telegram_bot.models import TelegramSettings

class Command(BaseCommand):
    help = 'Initialize empty Telegram settings in database'

    def handle(self, *args, **options):
        if TelegramSettings.objects.exists():
            self.stdout.write(self.style.WARNING("Telegram settings already exist in the database"))
            return

        telegram_settings = TelegramSettings.objects.create(
            bot_token="",
            admin_chat_id="",
            is_active=True
        )

        self.stdout.write(self.style.SUCCESS(
            f"Successfully initialized empty Telegram settings (ID: {telegram_settings.id}). "
            f"Please configure them in the admin panel."
        ))