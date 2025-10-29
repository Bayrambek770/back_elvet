from django.apps import AppConfig


class SupportRequestsConfig(AppConfig):
    """App configuration for support/callback requests management."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "support_requests"
    verbose_name = "Support Requests"
