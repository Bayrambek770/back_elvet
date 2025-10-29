from __future__ import annotations

from django.contrib import admin, messages
from django.utils import timezone

from .models import TelegramAnnouncement
from .tasks import send_announcement_broadcast


@admin.register(TelegramAnnouncement)
class TelegramAnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "sent_by", "sent_at", "target_count")
    search_fields = ("title", "message")
    readonly_fields = ("sent_at", "target_count")
    actions = ("broadcast_again",)

    @admin.action(description="Broadcast selected announcements again")
    def broadcast_again(self, request, queryset):
        count = 0
        for ann in queryset:
            # Update timestamp to now for a resend audit
            ann.sent_at = timezone.now()
            ann.save(update_fields=["sent_at"])
            send_announcement_broadcast.delay(ann.id)
            count += 1
        self.message_user(request, f"Triggered broadcast for {count} announcement(s).", messages.SUCCESS)
