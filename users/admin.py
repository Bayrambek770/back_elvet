from django.contrib import admin
from django.contrib.auth.hashers import identify_hasher

from .models import User, Admin as AdminProfile, Moderator, Doctor, Nurse, Client


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "first_name", "last_name", "role", "is_active", "date_joined")
    list_filter = ("role", "is_active")
    search_fields = ("phone_number", "first_name", "last_name")

    def _is_hashed(self, value: str | None) -> bool:
        if not value:
            return False
        try:
            identify_hasher(value)
            return True
        except Exception:
            return False

    def save_model(self, request, obj, form, change):
        """Ensure passwords are hashed when creating/editing users via Admin.

        If the provided password isn't a recognized hash, hash it before saving.
        """
        # form.cleaned_data may not have 'password' for all changes; rely on obj.password
        if obj.password and not self._is_hashed(obj.password):
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ("user",)


@admin.register(Moderator)
class ModeratorAdmin(admin.ModelAdmin):
    list_display = ("user", "work_start_date", "salary", "active", "created_by")
    list_filter = ("active",)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("user", "specialization", "work_start_date", "salary_per_case", "active", "created_by")
    list_filter = ("active", "specialization")


@admin.register(Nurse)
class NurseAdmin(admin.ModelAdmin):
    list_display = ("user", "work_start_date", "salary_per_day", "total_salary", "active", "created_by")
    list_filter = ("active",)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "extra_phone_number",
        "address",
        "telegram_id",
        "is_verified_via_telegram",
        "created_at",
        "created_by",
    )
    list_filter = ("is_verified_via_telegram",)
