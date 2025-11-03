"""Signals for the users app.

Currently: auto-create a Client profile when a new User with role=client is created.
"""
from __future__ import annotations

from typing import Any
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from decimal import Decimal
from django.utils import timezone

from .models import Client, RoleChoices, Admin as AdminProfile, Moderator, Doctor, Nurse

User = get_user_model()


@receiver(post_save, sender=User)
def create_role_profile_on_user_save(sender, instance: Any, created: bool, **kwargs):
    """Auto-create role profile objects based on the user's role.

    Runs on create and on subsequent saves (idempotent). If a profile already
    exists, nothing is created. Uses minimal safe defaults for required fields
    so admins can fill in details later.
    """
    try:
        today = timezone.localdate()
        role = getattr(instance, "role", None)

        if role == RoleChoices.CLIENT and not hasattr(instance, "client_profile"):
            Client.objects.create(user=instance)

        elif role == RoleChoices.ADMIN and not hasattr(instance, "admin_profile"):
            AdminProfile.objects.create(user=instance)

        elif role == RoleChoices.MODERATOR and not hasattr(instance, "moderator_profile"):
            Moderator.objects.create(
                user=instance,
                work_start_date=today,
                salary=Decimal("0"),
                created_by=None,
                active=True,
            )

        elif role == RoleChoices.DOCTOR and not hasattr(instance, "doctor_profile"):
            Doctor.objects.create(
                user=instance,
                specialization="",
                work_start_date=today,
                salary_per_case=Decimal("0"),
                created_by=None,
                active=True,
            )

        elif role == RoleChoices.NURSE and not hasattr(instance, "nurse_profile"):
            Nurse.objects.create(
                user=instance,
                work_start_date=today,
                salary_per_day=Decimal("0"),
                created_by=None,
                active=True,
            )
    except Exception:
        # Avoid cascading errors during user save; in production, log this.
        pass
