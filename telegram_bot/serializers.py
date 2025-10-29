from __future__ import annotations

from rest_framework import serializers
from users.models import Client


class ClientTelegramLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ["id", "telegram_id", "is_verified_via_telegram"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        # Ensure telegram_id uniqueness handled by model; add extra checks if needed
        return super().validate(attrs)
