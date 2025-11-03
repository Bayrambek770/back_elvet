"""Serializers for users and roles.

Provides ModelSerializers for User and role profile models.
"""

# Django/DRF imports
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Admin, Client, Doctor, Nurse, Moderator, RoleChoices

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the custom User model.

    Ensures password is write-only and hashed via set_password in create/update.
    """

    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "phone_number",
            "password",
            "role",
            "is_active",
            "telegram_id",
            "date_joined",
        )
        read_only_fields = ("id", "date_joined")

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class CreateUserSerializer(serializers.ModelSerializer):
    """Serializer dedicated for creating a new User via public API.

    Requires first_name, last_name, phone_number, password, and role.
    Password is write-only and will be hashed. Returns basic user info.
    """

    password = serializers.CharField(write_only=True, required=True, min_length=6)
    role = serializers.ChoiceField(choices=RoleChoices.choices, required=True)

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "phone_number",
            "password",
            "role",
            "date_joined",
        )
        read_only_fields = ("id", "date_joined")

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class AdminSerializer(serializers.ModelSerializer):
    """Serializer for Admin profile."""

    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source="user", queryset=User.objects.all(), write_only=True
    )

    class Meta:
        model = Admin
        fields = ("id", "user", "user_id")
        read_only_fields = ("id",)


class ModeratorSerializer(serializers.ModelSerializer):
    """Serializer for Moderator profile."""

    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source="user", queryset=User.objects.all(), write_only=True
    )
    created_by = AdminSerializer(read_only=True)
    created_by_id = serializers.PrimaryKeyRelatedField(
        source="created_by", queryset=Admin.objects.all(), write_only=True
    )

    class Meta:
        model = Moderator
        fields = (
            "id",
            "user",
            "user_id",
            "work_start_date",
            "salary",
            "created_by",
            "created_by_id",
            "active",
            "notes",
        )
        read_only_fields = ("id",)


class DoctorSerializer(serializers.ModelSerializer):
    """Serializer for Doctor profile."""

    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source="user", queryset=User.objects.all(), write_only=True
    )
    created_by = AdminSerializer(read_only=True)
    created_by_id = serializers.PrimaryKeyRelatedField(
        source="created_by", queryset=Admin.objects.all(), write_only=True
    )

    class Meta:
        model = Doctor
        fields = (
            "id",
            "user",
            "user_id",
            "specialization",
            "work_start_date",
            "salary_per_case",
            "active",
            "created_by",
            "created_by_id",
        )
        read_only_fields = ("id",)


class NurseSerializer(serializers.ModelSerializer):
    """Serializer for Nurse profile."""

    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source="user", queryset=User.objects.all(), write_only=True
    )
    created_by = AdminSerializer(read_only=True)
    created_by_id = serializers.PrimaryKeyRelatedField(
        source="created_by", queryset=Admin.objects.all(), write_only=True
    )

    class Meta:
        model = Nurse
        fields = (
            "id",
            "user",
            "user_id",
            "work_start_date",
            "salary_per_day",
            "total_salary",
            "rate_per_task",
            "experience_level",
            "active",
            "created_by",
            "created_by_id",
        )
        read_only_fields = ("id", "salary_per_day", "total_salary")


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for Client profile."""

    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source="user", queryset=User.objects.all(), write_only=True
    )
    created_by = ModeratorSerializer(read_only=True)
    created_by_id = serializers.PrimaryKeyRelatedField(
        source="created_by", queryset=Moderator.objects.all(), write_only=True
    )

    class Meta:
        model = Client
        fields = (
            "id",
            "user",
            "user_id",
            "extra_phone_number",
            "address",
            "created_at",
            "created_by",
            "created_by_id",
        )
        read_only_fields = ("id", "created_at")
