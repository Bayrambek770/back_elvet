from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import (
    Medicine,
    Service,
    Pet,
    MedicalCard,
    Payment,
    PaymentDay,
    Visit,
    StationaryRoom,
    Schedule,
    Task,
    NurseDailySalary,
    DoctorTask,
    DoctorIncome,
    NurseIncome,
)


class MedicalCardAdminForm(forms.ModelForm):
    """Admin form for MedicalCard with room filtering and date validation.

    Ensures only available rooms are selectable (including current on change view)
    and validates admission/release dates when assigning a room.
    """

    class Meta:
        model = MedicalCard
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, "instance", None)
        current_room = getattr(instance, "stationary_room", None) if instance and instance.pk else None

        # Filter stationary_room choices: free rooms + current (when editing)
        qs = StationaryRoom.objects.all()
        if current_room:
            self.fields["stationary_room"].queryset = qs.filter(
                Q(is_occupied=False) | Q(pk=current_room.pk)
            )
        else:
            self.fields["stationary_room"].queryset = qs.filter(is_occupied=False)

    def clean(self):
        cleaned = super().clean()
        room = cleaned.get("stationary_room")
        admission = cleaned.get("room_admission_date")
        release = cleaned.get("room_release_date")
        revisit = cleaned.get("revisit_date")
        instance = getattr(self, "instance", None)
        current_room = getattr(instance, "stationary_room", None) if instance and instance.pk else None

        # If selecting a new room, it must be available
        if room and (not current_room or room.pk != current_room.pk):
            if room.is_occupied:
                raise ValidationError({
                    "stationary_room": ["Selected room is not available (occupied)."],
                })
            if not admission:
                raise ValidationError({
                    "room_admission_date": ["Admission date is required when assigning a room."],
                })
        # Date ordering
        if admission and release and release < admission:
            raise ValidationError({
                "room_release_date": ["Release date cannot be earlier than admission date."],
            })
        # Revisit date cannot be in the past
        if revisit:
            from django.utils import timezone
            today = timezone.localdate()
            if revisit < today:
                raise ValidationError({
                    "revisit_date": ["Revisit date cannot be in the past."],
                })
        return cleaned


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ("name", "quantity", "original_price", "price", "expire_date")
    search_fields = ("name",)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "price")
    search_fields = ("name",)


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ("name", "breed", "client")
    search_fields = ("name", "breed")
    list_filter = ("gender",)


@admin.register(MedicalCard)
class MedicalCardAdmin(admin.ModelAdmin):
    form = MedicalCardAdminForm
    list_display = ("id", "client", "pet", "doctor", "nurse", "status", "total_fee", "created_at")
    list_filter = ("status", "doctor", "nurse")
    search_fields = ("diagnosis", "notes")

    def save_model(self, request, obj, form, change):
        """Apply room assignment side-effects: release/assign with dates."""
        # Capture previous room before saving changes
        old_room = None
        if obj.pk:
            try:
                old_room = MedicalCard.objects.get(pk=obj.pk).stationary_room
            except MedicalCard.DoesNotExist:  # pragma: no cover
                old_room = None

        super().save_model(request, obj, form, change)

        new_room = obj.stationary_room
        admission = obj.room_admission_date
        release = obj.room_release_date

        # Release the old room if it changed or was cleared
        if old_room and (not new_room or old_room.pk != new_room.pk):
            old_room.pet = None
            if release:
                old_room.release_date = release
            old_room.save()  # StationaryRoom.save() toggles is_occupied and timestamps

        # Assign the new room (link pet and set dates)
        if new_room:
            if new_room.is_occupied and new_room.pet_id not in (None, obj.pet_id):
                # Safety check; form should have prevented this
                raise ValidationError("Selected room is occupied by another pet.")
            # Ensure the pet isn't still linked to a different room (OneToOne safety)
            existing_room = StationaryRoom.objects.filter(pet=obj.pet).exclude(pk=new_room.pk).first()
            if existing_room:
                existing_room.pet = None
                if release:
                    existing_room.release_date = release
                existing_room.save()
            new_room.pet = obj.pet
            if admission:
                new_room.admission_date = admission
            if release:
                new_room.release_date = release
            if (
                new_room.admission_date
                and new_room.release_date
                and new_room.release_date < new_room.admission_date
            ):
                new_room.release_date = None
            new_room.save()


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("medical_card", "status", "method", "amount", "processed_by", "created_at")
    list_filter = ("status", "method")


@admin.register(StationaryRoom)
class StationaryRoomAdmin(admin.ModelAdmin):
    list_display = ("room_number", "is_occupied", "pet", "admission_date", "release_date")
    list_filter = ("is_occupied",)


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("id", "medical_card", "created_by", "assigned_nurse", "start_date", "end_date", "created_at")
    list_filter = ("start_date", "end_date", "assigned_nurse")
    search_fields = ("notes",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "schedule", "nurse", "day", "due_time", "is_done", "done_at")
    list_filter = ("is_done", "day", "nurse")
    search_fields = ("description",)


@admin.register(NurseDailySalary)
class NurseDailySalaryAdmin(admin.ModelAdmin):
    list_display = ("nurse", "date", "total_tasks", "completed_tasks", "salary")
    list_filter = ("date", "nurse")
    

@admin.register(DoctorTask)
class DoctorTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "doctor", "medical_card", "service", "is_done", "price", "created_at")
    list_filter = ("is_done", "doctor")
    search_fields = ("id", "doctor__user__first_name", "doctor__user__last_name")


@admin.register(DoctorIncome)
class DoctorIncomeAdmin(admin.ModelAdmin):
    list_display = ("doctor", "monthly_total", "last_reset")
    readonly_fields = ("monthly_total", "last_reset")


@admin.register(NurseIncome)
class NurseIncomeAdmin(admin.ModelAdmin):
    list_display = ("nurse", "daily_total", "monthly_total", "last_reset")
    readonly_fields = ("daily_total", "monthly_total", "last_reset")


@admin.register(PaymentDay)
class PaymentDayAdmin(admin.ModelAdmin):
    list_display = ("date", "price", "created_at")
    list_filter = ("date",)


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ("date", "client", "doctor", "reason", "created_at")
    list_filter = ("date", "doctor")
    search_fields = ("reason", "client__user__first_name", "client__user__last_name", "doctor__user__first_name", "doctor__user__last_name")
