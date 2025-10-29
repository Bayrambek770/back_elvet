"""Serializers for Request management."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Request
from .validators import validate_full_name, validate_phone_number, validate_text_length

User = get_user_model()


class RequestSerializer(serializers.ModelSerializer):
    """Serializer for Request with strong validation rules.

    - full_name: only letters and spaces
    - phone_number: international format; unique among open (is_answered=False) requests
    - text: up to 1000 chars
    - created_by: auto-assigned from request.user if authenticated
    """

    created_at_formatted = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Request
        fields = (
            "id",
            "full_name",
            "phone_number",
            "text",
            "created_at",
            "created_at_formatted",
            "is_answered",
            "answered_by",
        )
        read_only_fields = ("id", "created_at", "created_at_formatted", "is_answered", "answered_by")

    def validate_full_name(self, value: str) -> str:
        validate_full_name(value)
        return value

    def validate_phone_number(self, value: str) -> str:
        validate_phone_number(value)
        qs = Request.objects.filter(phone_number=value, is_answered=False)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "There is already an active (unanswered) request for this phone number.",
                code="duplicate_open_request",
            )
        return value

    def validate_text(self, value: str | None) -> str | None:
        validate_text_length(value)
        return value

    def get_created_at_formatted(self, obj: Request) -> str:
        return obj.created_at.isoformat()

    # Creation does not require authentication; requests can be anonymous
