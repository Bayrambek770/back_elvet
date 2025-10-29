from __future__ import annotations

import re
from typing import Optional

from django.conf import settings

from users.models import User, RoleChoices, Client


def normalize_phone(phone: str) -> str:
    """Normalize phone to +XXXXXXXXXXX format by stripping non-digits and ensuring + prefix."""
    digits = re.sub(r"\D+", "", phone)
    if not digits.startswith("+"):
        digits = "+" + digits
    return digits


def is_admin_or_moderator(telegram_user_id: int) -> bool:
    # Prefer mapping via Client to linked user
    cli = Client.objects.filter(telegram_id=telegram_user_id).select_related("user").first()
    if cli and cli.user and cli.user.role in [RoleChoices.ADMIN, RoleChoices.MODERATOR]:
        return True
    # Fallback: check User.telegram_id directly
    return User.objects.filter(
        telegram_id=str(telegram_user_id), role__in=[RoleChoices.ADMIN, RoleChoices.MODERATOR]
    ).exists()


def get_verified_client_ids() -> list[int]:
    return list(
        Client.objects.filter(is_verified_via_telegram=True).exclude(telegram_id__isnull=True).values_list(
            "telegram_id", flat=True
        )
    )
