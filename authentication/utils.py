"""Utility helpers for JWT token handling."""

from typing import Dict

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def generate_user_tokens(user) -> Dict[str, str]:
    """Generate a pair of JWT tokens (refresh and access) for a user.

    Returns dict with keys: refresh_token, access_token.
    """
    refresh = RefreshToken.for_user(user)
    return {
        "refresh_token": str(refresh),
        "access_token": str(refresh.access_token),
    }
