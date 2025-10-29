from django.contrib import admin

from .models import User, Admin as AdminProfile, Moderator, Doctor, Nurse, Client


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "first_name", "last_name", "role", "is_active", "date_joined")
    list_filter = ("role", "is_active")
    search_fields = ("phone_number", "first_name", "last_name")


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
