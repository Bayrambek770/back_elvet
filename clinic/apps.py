from django.apps import AppConfig


class ClinicConfig(AppConfig):
    """App configuration for clinic domain models."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "clinic"
    verbose_name = "Clinic"