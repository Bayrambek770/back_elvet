"""Models for support/callback requests."""

from django.conf import settings
from django.db import models

from .validators import validate_phone_number


class Request(models.Model):
    """A support or callback request submitted by a user.

    Only moderators can view/respond. Regular users can only create.
    """

    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, validators=[validate_phone_number])
    text = models.TextField(blank=True, null=True, max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    # Workflow fields
    is_answered = models.BooleanField(default=False)
    answered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="answered_support_requests",
        help_text="Moderator who handled the request",
    )

    # Note: No creator tracking; requests can be anonymous.

    class Meta:
        verbose_name = "Request"
        verbose_name_plural = "Requests"
        ordering = ("-created_at",)

    def __str__(self) -> str:  # pragma: no cover - simple representation
        status = "answered" if self.is_answered else "open"
        return f"{self.full_name} - {self.phone_number} ({status})"
