"""Signals for the users app.

Currently: auto-create a Client profile when a new User with role=client is created.
"""
from __future__ import annotations

from typing import Any
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Client, RoleChoices

User = get_user_model()


@receiver(post_save, sender=User)
def create_client_on_user_create(sender, instance: Any, created: bool, **kwargs):
    """Auto-create a Client profile for newly created users with client role.

    Address and created_by remain optional and can be set later.
    """
    if not created:
        return
    try:
        if instance.role == RoleChoices.CLIENT and not hasattr(instance, "client_profile"):
            Client.objects.create(user=instance)
    except Exception:
        # Avoid cascading errors during user creation; log in real deployments
        pass
