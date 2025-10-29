"""Serializers for clinic domain models.

Provides ModelSerializers for Pet, Medicine, Service, MedicalCard, Payment,
StationaryRoom with nested relationships where meaningful.
"""

# DRF imports
from rest_framework import serializers

# App imports
from users.serializers import ClientSerializer, DoctorSerializer, NurseSerializer, ModeratorSerializer
from .models import (
    MedicalCard,
    Medicine,
    NurseDailySalary,
    Payment,
    Pet,
    Schedule,
    Service,
    Task,
    StationaryRoom,
)


class PetSerializer(serializers.ModelSerializer):
    """Serializer for Pet model."""

    client = ClientSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(
        source="client", queryset=ClientSerializer.Meta.model.objects.all(), write_only=True
    )

    class Meta:
        model = Pet
        fields = (
            "id",
            "client",
            "client_id",
            "name",
            "breed",
            "age",
            "gender",
            "notes",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class MedicineSerializer(serializers.ModelSerializer):
    """Serializer for Medicine model."""

    class Meta:
        model = Medicine
        fields = (
            "id",
            "name",
            "quantity",
            "original_price",
            "price",
            "expire_date",
            "description",
            "created_by",
        )
        read_only_fields = ("id",)


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for Service model."""

    class Meta:
        model = Service
        fields = (
            "id",
            "name",
            "price",
            "description",
            "created_by",
        )
        read_only_fields = ("id",)


class StationaryRoomSerializer(serializers.ModelSerializer):
    """Serializer for StationaryRoom."""

    pet = PetSerializer(read_only=True)
    pet_id = serializers.PrimaryKeyRelatedField(
        source="pet", queryset=Pet.objects.all(), write_only=True, allow_null=True, required=False
    )

    class Meta:
        model = StationaryRoom
        fields = (
            "id",
            "room_number",
            "is_occupied",
            "pet",
            "pet_id",
            "admission_date",
            "release_date",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def validate(self, attrs):
        # Only allow assigning a pet to a free room
        pet = attrs.get("pet")
        instance = getattr(self, "instance", None)
        is_occupied = getattr(instance, "is_occupied", False) if instance else False
        if pet and instance and is_occupied and instance.pet_id != getattr(pet, "id", None):
            raise serializers.ValidationError({"pet_id": "This room is already occupied."})
        return attrs


class MedicalCardSerializer(serializers.ModelSerializer):
    """Serializer for MedicalCard with nested relationships.

    Provides nested read-only representations and accepts IDs for writes.
    """

    client = ClientSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(
        source="client", queryset=ClientSerializer.Meta.model.objects.all(), write_only=True
    )
    pet = PetSerializer(read_only=True)
    pet_id = serializers.PrimaryKeyRelatedField(
        source="pet", queryset=Pet.objects.all(), write_only=True
    )
    doctor = DoctorSerializer(read_only=True)
    doctor_id = serializers.PrimaryKeyRelatedField(
        source="doctor", queryset=DoctorSerializer.Meta.model.objects.all(), write_only=True
    )
    nurse = NurseSerializer(read_only=True)
    nurse_id = serializers.PrimaryKeyRelatedField(
        source="nurse",
        queryset=NurseSerializer.Meta.model.objects.all(),
        write_only=True,
        allow_null=True,
        required=False,
    )

    services = ServiceSerializer(many=True, read_only=True)
    medicines = MedicineSerializer(many=True, read_only=True)

    stationary_room = StationaryRoomSerializer(read_only=True)
    stationary_room_id = serializers.PrimaryKeyRelatedField(
        source="stationary_room",
        queryset=StationaryRoom.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    # room_admission_date and room_release_date are model fields; DRF maps them automatically

    service_ids = serializers.PrimaryKeyRelatedField(
        source="services", queryset=Service.objects.all(), many=True, write_only=True, required=False
    )
    medicine_ids = serializers.PrimaryKeyRelatedField(
        source="medicines", queryset=Medicine.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = MedicalCard
        fields = (
            "id",
            # core relations
            "client", "client_id",
            "pet", "pet_id",
            "doctor", "doctor_id",
            "nurse", "nurse_id",
            # stationary room
            "stationary_room", "stationary_room_id",
            "room_admission_date", "room_release_date",
            # chargeables
            "services", "service_ids",
            "medicines", "medicine_ids",
            # card details
            "status", "diagnosis", "notes",
            # timestamps and totals
            "created_at", "closed_at", "total_fee",
        )
        read_only_fields = ("id", "created_at", "closed_at", "total_fee")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show only available rooms by default; include current room on update
        current_room_id = getattr(self.instance, "stationary_room_id", None) if self.instance else None
        qs = StationaryRoom.objects.all()
        if current_room_id:
            from django.db.models import Q
            self.fields["stationary_room_id"].queryset = qs.filter(Q(is_occupied=False) | Q(pk=current_room_id))
        else:
            self.fields["stationary_room_id"].queryset = qs.filter(is_occupied=False)

    def create(self, validated_data):
        services = validated_data.pop("services", [])
        medicines = validated_data.pop("medicines", [])
        card = super().create(validated_data)
        if services:
            card.services.set(services)
        if medicines:
            card.medicines.set(medicines)
        # Stationary room: ensure availability, set pet linkage and dates
        self._apply_stationary_room_updates(card)
        # Ensure total fee is correct after relations are set
        card.update_total_fee()
        return card

    def update(self, instance, validated_data):
        services = validated_data.pop("services", None)
        medicines = validated_data.pop("medicines", None)
        old_room = instance.stationary_room
        card = super().update(instance, validated_data)
        if services is not None:
            card.services.set(services)
        if medicines is not None:
            card.medicines.set(medicines)
        # Release previous room if changed or cleared
        if old_room and (not card.stationary_room or card.stationary_room.id != old_room.id):
            old_room.pet = None
            # If explicit release date provided on card, apply; otherwise model save() will timestamp now
            if card.room_release_date:
                old_room.release_date = card.room_release_date
            # Let model toggle occupancy and set release timestamp
            old_room.save()
        self._apply_stationary_room_updates(card)
        card.update_total_fee()
        return card

    def validate(self, attrs):
        # Ensure selected pet belongs to the selected client
        client = attrs.get("client") or getattr(self.instance, "client", None)
        pet = attrs.get("pet") or getattr(self.instance, "pet", None)
        if client and pet and pet.client_id != client.id:
            raise serializers.ValidationError({"pet_id": "Selected pet does not belong to the selected client."})
        # Revisit date cannot be in the past
        revisit_date = attrs.get("revisit_date")
        if revisit_date:
            from django.utils import timezone
            today = timezone.localdate()
            if revisit_date < today:
                raise serializers.ValidationError({"revisit_date": "Revisit date cannot be in the past."})
        # Stationary room must be available if being assigned/changed; validate dates
        new_room = attrs.get("stationary_room")
        current_room = getattr(self.instance, "stationary_room", None)
        admission = attrs.get("room_admission_date")
        release = attrs.get("room_release_date")
        if new_room and (not current_room or current_room.id != new_room.id):
            if new_room.is_occupied:
                raise serializers.ValidationError({
                    "stationary_room_id": "Selected room is not available (occupied).",
                })
            if not admission:
                raise serializers.ValidationError({
                    "room_admission_date": "Admission date is required when assigning a room.",
                })
        if admission and release and release < admission:
            raise serializers.ValidationError({
                "room_release_date": "Release date cannot be earlier than admission date.",
            })
        return attrs

    def _apply_stationary_room_updates(self, card: MedicalCard):
        """Bind the pet to the selected room and set dates.

        Relies on StationaryRoom.save() to toggle occupancy and timestamps.
        """
        room = card.stationary_room
        if not room:
            return
        # Assign the pet to the room if free or already bound to same pet
        if room.is_occupied and room.pet_id not in (None, card.pet_id):
            # Another pet occupies the room; validation should have blocked earlier
            return
        # Ensure the pet isn't still linked to a different room (OneToOne safety)
        existing_room = StationaryRoom.objects.filter(pet=card.pet).exclude(pk=room.pk).first()
        if existing_room:
            existing_room.pet = None
            # Optionally set release date from card if provided
            if card.room_release_date:
                existing_room.release_date = card.room_release_date
            existing_room.save()
        # Link pet; let model toggle occupancy and timestamps
        room.pet = card.pet
        # Respect provided dates from medical card; fall back to auto if not provided
        if card.room_admission_date:
            room.admission_date = card.room_admission_date
        if card.room_release_date:
            room.release_date = card.room_release_date
        # If release_date is set and is before admission, clear it
        if room.admission_date and room.release_date and room.release_date < room.admission_date:
            room.release_date = None
        room.save()


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""

    medical_card = MedicalCardSerializer(read_only=True)
    medical_card_id = serializers.PrimaryKeyRelatedField(
        source="medical_card", queryset=MedicalCard.objects.all(), write_only=True
    )

    processed_by = ModeratorSerializer(read_only=True)
    processed_by_id = serializers.PrimaryKeyRelatedField(
        source="processed_by",
        queryset=ModeratorSerializer.Meta.model.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Payment
        fields = (
            "id",
            "medical_card",
            "medical_card_id",
            "status",
            "method",
            "processed_by",
            "processed_by_id",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


 


class ScheduleSerializer(serializers.ModelSerializer):
    """Serializer for Schedule model with validation for date range."""

    medical_card_id = serializers.PrimaryKeyRelatedField(
        source="medical_card", queryset=MedicalCard.objects.all(), write_only=True
    )
    created_by_id = serializers.PrimaryKeyRelatedField(
        source="created_by", queryset=DoctorSerializer.Meta.model.objects.all(), write_only=True
    )
    assigned_nurse_id = serializers.PrimaryKeyRelatedField(
        source="assigned_nurse", queryset=NurseSerializer.Meta.model.objects.all(), write_only=True
    )

    medical_card = serializers.PrimaryKeyRelatedField(read_only=True)
    created_by = DoctorSerializer(read_only=True)
    assigned_nurse = NurseSerializer(read_only=True)

    class Meta:
        model = Schedule
        fields = (
            "id",
            "medical_card",
            "medical_card_id",
            "created_by",
            "created_by_id",
            "assigned_nurse",
            "assigned_nurse_id",
            "start_date",
            "end_date",
            "created_at",
            "notes",
        )
        read_only_fields = ("id", "created_at")

    def validate(self, attrs):
        start = attrs.get("start_date") or getattr(self.instance, "start_date", None)
        end = attrs.get("end_date") or getattr(self.instance, "end_date", None)
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "End date cannot be earlier than start date."})
        return attrs


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task with consistency checks."""

    schedule_id = serializers.PrimaryKeyRelatedField(
        source="schedule", queryset=Schedule.objects.all(), write_only=True
    )
    nurse_id = serializers.PrimaryKeyRelatedField(
        source="nurse", queryset=NurseSerializer.Meta.model.objects.all(), write_only=True
    )

    schedule = serializers.PrimaryKeyRelatedField(read_only=True)
    nurse = NurseSerializer(read_only=True)

    class Meta:
        model = Task
        fields = (
            "id",
            "schedule",
            "schedule_id",
            "nurse",
            "nurse_id",
            "description",
            "day",
            "due_time",
            "is_done",
            "done_at",
        )
        read_only_fields = ("id", "done_at")

    def validate(self, attrs):
        schedule = attrs.get("schedule") or getattr(self.instance, "schedule", None)
        nurse = attrs.get("nurse") or getattr(self.instance, "nurse", None)
        day = attrs.get("day") or getattr(self.instance, "day", None)
        # Nurse must be the schedule's assigned nurse
        if schedule and nurse and schedule.assigned_nurse_id != nurse.id:
            raise serializers.ValidationError({"nurse_id": "Nurse must match the schedule's assigned nurse."})
        # Task day must be within schedule date range
        if schedule and day and (day < schedule.start_date or day > schedule.end_date):
            raise serializers.ValidationError({"day": "Task day must be within the schedule date range."})
        return attrs


class NurseDailySalarySerializer(serializers.ModelSerializer):
    """Read-only serializer for daily nurse salary and stats."""

    nurse = NurseSerializer(read_only=True)

    class Meta:
        model = NurseDailySalary
        fields = (
            "id",
            "nurse",
            "date",
            "total_tasks",
            "completed_tasks",
            "salary",
        )
        read_only_fields = fields
