import os
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from telegram_bot.services.bot_service import BotService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Запускает Telegram бота'

    def handle(self, *args, **options):
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', os.environ.get('TELEGRAM_BOT_TOKEN'))

        if not token:
            self.stderr.write(self.style.ERROR(
                'Не указан токен бота. Установите TELEGRAM_BOT_TOKEN в settings.py или в переменных окружения.'))
            return

        self.stdout.write(self.style.SUCCESS('Запуск Telegram бота...'))

        try:
            bot_service = BotService(token)
            bot_service.start()
        except Exception as e:
            logger.exception("Критическая ошибка при запуске бота")
            self.stderr.write(self.style.ERROR(f'Ошибка при запуске бота: {e}'))