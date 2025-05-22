from django.contrib import admin
from .models import TelegramSettings

# Register your models here.


@admin.register(TelegramSettings)
class TelegramSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_active', 'updated_at')
    list_filter = ('is_active', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('bot_token', 'admin_chat_id', 'is_active')
        }),
        ('Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_delete_permission(self, request, obj=None):
        if obj and TelegramSettings.objects.count() <= 1:
            return False
        return super().has_delete_permission(request, obj)