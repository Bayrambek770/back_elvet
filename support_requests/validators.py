"""Custom validators for the support_requests app."""

import re
from typing import Any

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Accepts strictly international E.164-like formats with '+' prefix.
# - Uzbek numbers: +998XXXXXXXXX (9 digits after 998)
# - Other international: +[country][subscriber], total length 9-15 digits after '+'
PHONE_REGEX = re.compile(r"^\+(?:998\d{9}|[1-9]\d{7,14})$")


def validate_phone_number(value: str) -> None:
    """Validate phone number format for requests.

    Enforces leading '+' and either a valid Uzbek number (+998XXXXXXXXX) or a
    general international number with a total of 9-15 digits after '+'.
    """
    if not PHONE_REGEX.match(value or ""):
        raise ValidationError(
            _("Enter a valid phone number in international format (e.g., +998XXYYYYYYY)."),
            code="invalid_phone",
        )


def validate_full_name(value: str) -> None:
    """Validate full name contains only alphabetic characters and spaces.

    Supports Unicode letters; trims multiple spaces.
    """
    if not value:
        raise ValidationError(_("Full name is required."), code="required")
    compact = value.replace(" ", "")
    if not compact.isalpha():
        raise ValidationError(
            _("Full name must contain only letters and spaces."),
            code="invalid_name",
        )


def validate_text_length(value: Any) -> None:
    """Ensure the optional text is not overly long (>1000)."""
    if value and len(value) > 1000:
        raise ValidationError(_("Text must be at most 1000 characters."), code="max_length")
