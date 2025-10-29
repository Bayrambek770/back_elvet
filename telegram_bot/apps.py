from django.apps import AppConfig


class TelegramBotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "telegram_bot"
    verbose_name = "Telegram Bot"

    def ready(self) -> None:  # pragma: no cover
        # Import signals if we add any later
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
