from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Request

User = get_user_model()


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone_number", "is_answered", "created_at", "answered_by")
    list_filter = ("is_answered", "created_at")
    search_fields = ("full_name", "phone_number", "text")
    readonly_fields = ("created_at",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "answered_by":
            # Show only moderators in admin select
            kwargs["queryset"] = User.objects.filter(role="moderator")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
