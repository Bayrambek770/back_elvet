"""Serializers for JWT authentication flows (register, login, refresh, logout)."""

from django.contrib.auth import get_user_model, authenticate
from django.core.validators import RegexValidator
from rest_framework import serializers

from .utils import generate_user_tokens

User = get_user_model()


class PublicUserSerializer(serializers.ModelSerializer):
    """Public-facing user serializer with limited fields for responses."""

    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "phone_number", "role")
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """Register new users with phone-number and password.

    Only allows creating client accounts by default (safe registration path).
    """

    password = serializers.CharField(write_only=True, min_length=6)
    phone_number = serializers.CharField(
        validators=[RegexValidator(r"^\+?[0-9]{9,15}$", "Enter a valid phone number.")]
    )

    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "phone_number", "password")
        read_only_fields = ("id",)

    def validate_phone_number(self, value: str) -> str:
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("This phone number is already registered.")
        return value

    def create(self, validated_data):
        # Role defaults to model's default (client) to ensure safe registration path
        user = User(
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            phone_number=validated_data["phone_number"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Validate login credentials and return tokens + user payload."""

    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        phone_number = attrs.get("phone_number")
        password = attrs.get("password")
        # Django's ModelBackend expects `username` param; our USERNAME_FIELD is phone_number
        user = authenticate(self.context.get("request"), username=phone_number, password=password)
        if not user:
            # Fallback manual check when custom auth backends behave differently
            try:
                user_obj = User.objects.get(phone_number=phone_number)
                if not user_obj.check_password(password):
                    raise User.DoesNotExist
                user = user_obj
            except User.DoesNotExist:  # noqa: B904
                raise serializers.ValidationError({
                    "detail": "Invalid phone number or password.",
                    "code": "invalid_credentials",
                })
        if not user.is_active:
            raise serializers.ValidationError({
                "detail": "User account is disabled.",
                "code": "inactive_account",
            })
        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        tokens = generate_user_tokens(user)
        return {
            **tokens,
            "user": PublicUserSerializer(user).data,
        }


class RefreshSerializer(serializers.Serializer):
    """Accept a refresh token and return a new access token."""

    refresh = serializers.CharField(write_only=True)


class LogoutSerializer(serializers.Serializer):
    """Accept a refresh token to blacklist (logout)."""

    refresh = serializers.CharField(write_only=True)
