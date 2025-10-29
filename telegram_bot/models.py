from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class TelegramAnnouncement(models.Model):
    """Log of announcements sent via Telegram.

    Stores content, sender, and delivery stats for auditing and resends.
    """

    title = models.CharField(max_length=255)
    message = models.TextField()
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="sent_announcements"
    )
    sent_at = models.DateTimeField(default=timezone.now)
    target_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("-sent_at",)
        verbose_name = "Telegram Announcement"
        verbose_name_plural = "Telegram Announcements"

    def __str__(self) -> str:
        return f"{self.title} ({self.sent_at:%Y-%m-%d %H:%M})"
