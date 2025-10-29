from django.apps import AppConfig


class UsersConfig(AppConfig):
    """App configuration for users app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
    verbose_name = "Users and Roles" 

    def ready(self) -> None:  # pragma: no cover - side-effect import
        # Import signals to ensure they are registered when the app is ready
        try:
            from . import signals  # noqa: F401
        except Exception:
            # Avoid import-time failures taking down the app; log in production
            pass
