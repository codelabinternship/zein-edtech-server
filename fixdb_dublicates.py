from telegram_bot.models import TelegramUser
from django.db.models import Count

duplicates = TelegramUser.objects.values('telegram_id').annotate(
    count=Count('id')
).filter(count__gt=1)

for dup in duplicates:
    users = TelegramUser.objects.filter(telegram_id=dup['telegram_id'])
    users.exclude(id=users.first().id).delete()
