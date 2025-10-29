from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """App configuration for custom JWT authentication."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "authentication"
    verbose_name = "Authentication"
