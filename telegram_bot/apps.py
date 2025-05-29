from django.apps import AppConfig


class TelegramBotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'telegram_bot'


from django.apps import AppConfig


class TelegramBotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'telegram_bot'

    def ready(self):
        from django.db.models.signals import post_migrate
        from django.dispatch import receiver

        @receiver(post_migrate)
        def create_initial_settings(sender, **kwargs):
            if sender.name == self.name:
                from telegram_bot.models import TelegramSettings

                if not TelegramSettings.objects.exists():
                    TelegramSettings.objects.create(
                        bot_token="CONFIGURE_ME_IN_ADMIN_PANEL",
                        admin_chat_id="CONFIGURE_ME_IN_ADMIN_PANEL",
                        is_active=True
                    )
                    print("Created initial Telegram settings. Please configure them in admin panel.")