from django.db import models

# Create your models here.

# from account.models import User
from django.conf import settings

class TelegramUser(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    telegram_id = models.BigIntegerField(unique=True)
    chat_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    language_code = models.CharField(max_length=10, default='ru')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.telegram_id})"

    class Meta:
        verbose_name = "Telegram user"
        verbose_name_plural = "Telegram users"





class TelegramSettings(models.Model):
    bot_token = models.CharField(max_length=255, verbose_name="Request bot token")
    admin_chat_id = models.CharField(max_length=50, verbose_name="ID chat admin")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Settings RequestTelegram bot"
        verbose_name_plural = "Settings RequestTelegram bot"

    def __str__(self):
        return f"Settings Request bot (ID: {self.id})"

    def clean(self):
        if self.is_active:
            active_settings = TelegramSettings.objects.filter(is_active=True).exclude(id=self.id)
            if active_settings.exists():
                active_settings.update(is_active=False)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_active(cls):
        try:
            return cls.objects.get(is_active=True)
        except cls.DoesNotExist:
            return None