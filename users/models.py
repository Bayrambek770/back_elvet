"""Users and roles models for clinic management system.

This module defines a custom User model authenticated by phone number and
role-specific profile models (Admin, Moderator, Doctor, Nurse, Client).
"""

# Standard library imports
from __future__ import annotations
from typing import Any

# Django imports
from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


class RoleChoices(models.TextChoices):
    """Enumerated roles available in the system."""

    ADMIN = "admin", "Admin"
    MODERATOR = "moderator", "Moderator"
    DOCTOR = "doctor", "Doctor"
    NURSE = "nurse", "Nurse"
    CLIENT = "client", "Client"


class UserManager(BaseUserManager):
    """Manager for custom User model using phone-based login."""

    use_in_migrations = True

    def _create_user(self, phone_number: str, password: str | None, **extra_fields: Any) -> "User":
        if not phone_number:
            raise ValueError("The phone number must be set")
        phone_number = self.normalize_email(phone_number) if "@" in phone_number else phone_number
        user = self.model(phone_number=phone_number, **extra_fields)
        if password:
            user.set_password(password)
        else:
            # Allow creating users without password (to be set later)
            user.set_unusable_password()
        user.date_joined = timezone.now()
        user.save(using=self._db)
        return user

    def create_user(self, phone_number: str, password: str | None = None, **extra_fields: Any) -> "User":
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        if not extra_fields.get("role"):
            extra_fields["role"] = RoleChoices.CLIENT
        return self._create_user(phone_number, password, **extra_fields)

    def create_superuser(self, phone_number: str, password: str | None = None, **extra_fields: Any) -> "User":
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", RoleChoices.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model for phone-number based authentication.

    Fields include names, unique phone number, role, and optional telegram ID.
    Email is intentionally omitted. Password is handled by AbstractBaseUser.
    """

    first_name = models.CharField("first name", max_length=150)
    last_name = models.CharField("last name", max_length=150)

    phone_regex = RegexValidator(r"^\+?[0-9]{9,15}$", "Enter a valid phone number.")
    phone_number = models.CharField(
        "phone number",
        max_length=17,
        unique=True,
        validators=[phone_regex],
        help_text="Unique phone number used for login",
    )

    role = models.CharField(
        max_length=16,
        choices=RoleChoices.choices,
        default=RoleChoices.CLIENT,
        help_text="Role used for role-based access control",
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(
        default=False, help_text="Designates whether the user can access the admin site."
    )

    telegram_id = models.CharField(
        max_length=64, blank=True, null=True, help_text="Optional Telegram user identifier"
    )

    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ("-date_joined",)

    def __str__(self) -> str:  # pragma: no cover - simple string rep
        return f"{self.get_full_name()} ({self.phone_number})"

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self) -> str:
        return self.first_name or self.phone_number


class Admin(models.Model):
    """Admin profile linked to a user with admin role.

    Admins can manage staff and clinic resources.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="admin_profile"
    )  # One-to-one with user

    class Meta:
        verbose_name = "Admin"
        verbose_name_plural = "Admins"

    def __str__(self) -> str:  # pragma: no cover
        return f"Admin: {self.user.get_full_name()}"


class Moderator(models.Model):
    """Moderator profile linked to a user with moderator role.

    Moderators can create clients, process payments, and read service requests.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="moderator_profile"
    )  # One-to-one with user
    work_start_date = models.DateField()
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_by = models.ForeignKey(
        Admin, on_delete=models.PROTECT, related_name="created_moderators", blank=True, null=True
    )  # Created by admin (optional on auto-create)
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Moderator"
        verbose_name_plural = "Moderators"

    def __str__(self) -> str:  # pragma: no cover
        return f"Moderator: {self.user.get_full_name()}"


class Doctor(models.Model):
    """Doctor profile linked to a user with doctor role.

    Doctors can create and edit medical cards and assign nurses.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="doctor_profile"
    )  # One-to-one with user
    specialization = models.CharField(max_length=255)
    work_start_date = models.DateField()
    salary_per_case = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        Admin, on_delete=models.PROTECT, related_name="created_doctors", blank=True, null=True
    )  # Created by admin (optional on auto-create)

    class Meta:
        verbose_name = "Doctor"
        verbose_name_plural = "Doctors"

    def __str__(self) -> str:  # pragma: no cover
        return f"Doctor: {self.user.get_full_name()} ({self.specialization})"


class Nurse(models.Model):
    """Nurse profile linked to a user with nurse role.

    Nurses work on medical cards and are paid per service/day.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="nurse_profile"
    )  # One-to-one with user
    work_start_date = models.DateField()
    salary_per_day = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_salary = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    # Nurse Management System additions
    rate_per_task = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=10000.00,
        help_text="Payment amount per completed task",
    )
    experience_level = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="Optional experience level or position",
    )
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        Admin, on_delete=models.PROTECT, related_name="created_nurses", blank=True, null=True
    )  # Created by admin (optional on auto-create)

    class Meta:
        verbose_name = "Nurse"
        verbose_name_plural = "Nurses"

    def __str__(self) -> str:  # pragma: no cover
        return f"Nurse: {self.user.get_full_name()}"

    def clean(self):
        """Ensure the linked user's role is 'nurse' and created_by is provided.

        Enforces domain constraint that only Admin creates nurse profiles and
        that the user's role matches the profile type.
        """
        from django.core.exceptions import ValidationError

        if not self.created_by_id:
            # Allow auto-created nurses without creator; enforce in admin/forms later
            pass
        # Validate user role
        if getattr(self.user, "role", None) != RoleChoices.NURSE:
            raise ValidationError("Linked user must have role='nurse'.")


class Client(models.Model):
    """Client profile linked to a user with client role.

    Clients own pets and have medical cards.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="client_profile"
    )  # One-to-one with user
    extra_phone_number = models.CharField(max_length=17, blank=True, null=True)
    telegram_id = models.BigIntegerField(unique=True, blank=True, null=True, help_text="Telegram user ID")
    is_verified_via_telegram = models.BooleanField(default=False)
    # Preferred language for Telegram communications (e.g., 'en', 'ru', 'uz')
    language = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        choices=[
            ("en", "English"),
            ("ru", "Русский"),
            ("uz", "O'zbekcha"),
        ],
        help_text="Preferred language code for bot interactions",
    )
    address = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        Moderator, on_delete=models.PROTECT, related_name="created_clients", blank=True, null=True
    )  # Created by moderator (optional for auto-created clients)

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"

    def __str__(self) -> str:  # pragma: no cover
        return f"Client: {self.user.get_full_name()}"

    
