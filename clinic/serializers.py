"""Serializers for clinic domain models.

Provides ModelSerializers for Pet, Medicine, Service, MedicalCard, Payment,
StationaryRoom with nested relationships where meaningful.
"""

# DRF imports
from rest_framework import serializers
from decimal import Decimal

# App imports
from users.serializers import ClientSerializer, DoctorSerializer, NurseSerializer, ModeratorSerializer
from .models import (
    MedicalCard,
    MedicalCardService,
    Medicine,
    NurseDailySalary,
    Payment,
    Pet,
    Schedule,
    Service,
    Task,
    StationaryRoom,
    DoctorTask,
    DoctorIncome,
    NurseIncome,
    PaymentDay,
    Visit,
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
            "animal_type",
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
            "price_up_to",
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


class ServicePriceSelectionSerializer(serializers.Serializer):
    """Schema for selecting a service with a custom price on a medical card.

    Helps OpenAPI (Swagger) display proper field structure instead of free-form dicts.
    """

    service_id = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())
    price = serializers.DecimalField(max_digits=12, decimal_places=2)


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

    # Present services via the M2M, which we keep in sync with priced selections
    services = ServiceSerializer(many=True, read_only=True)
    # Selected services with chosen prices
    services_selected = serializers.SerializerMethodField(read_only=True)
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
    # New format allowing custom price per service
    services_priced = ServicePriceSelectionSerializer(many=True, write_only=True, required=False,
        help_text="List of {service_id, price} pairs to set custom prices for selected services.")
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
            "services", "services_selected", "service_ids", "services_priced",
            "medicines", "medicine_ids",
            # card details
            "status",
            # vitals and clinical observations
            "weight", "blood_pressure", "mucous_membrane", "heart_rate", "respiratory_rate",
            "general_condition", "chest_condition", "body_temperature",
            # clinical texts
            "anamnesis", "diagnosis", "diet", "notes",
            # revisit
            "revisit_date",
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
        services_priced = self.initial_data.get("services_priced") if isinstance(self.initial_data, dict) else None
        # Apply priced selections if provided; else fallback to plain set
        if services_priced:
            selected_services = self._apply_services_priced(card, services_priced)
            # Keep M2M membership in sync for read APIs
            card.services.set(selected_services)
        elif services:
            # Back-compat: set selections with fixed price from service
            for svc in services:
                MedicalCardService.objects.update_or_create(
                    medical_card=card, service=svc, defaults={"price": svc.price}
                )
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
        services_priced = self.initial_data.get("services_priced") if isinstance(self.initial_data, dict) else None
        if services_priced is not None:
            # Replace selections per request
            MedicalCardService.objects.filter(medical_card=card).delete()
            if services_priced:
                selected_services = self._apply_services_priced(card, services_priced)
                card.services.set(selected_services)
            else:
                card.services.clear()
        elif services is not None:
            MedicalCardService.objects.filter(medical_card=card).delete()
            for svc in services:
                MedicalCardService.objects.update_or_create(
                    medical_card=card, service=svc, defaults={"price": svc.price}
                )
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

    def get_services_selected(self, obj: MedicalCard):
        items = []
        for link in obj.service_links.select_related("service").all():
            items.append({
                "service": ServiceSerializer(link.service).data,
                "price": str(link.price),
            })
        return items

    def _apply_services_priced(self, card: MedicalCard, selections):
        """Create priced service links with validation.

        selections: list of dicts {service_id, price}
        """
        from decimal import Decimal as D
        selected_services = []
        for sel in selections:
            svc_id = sel.get("service_id")
            price = sel.get("price")
            if svc_id is None or price is None:
                raise serializers.ValidationError({"services_priced": "Each item must include service_id and price."})
            try:
                svc = Service.objects.get(pk=svc_id)
            except Service.DoesNotExist:
                raise serializers.ValidationError({"services_priced": f"Service {svc_id} not found."})
            price = D(str(price))
            # Validate price bounds
            if svc.price_up_to is None:
                if price != svc.price:
                    raise serializers.ValidationError({"services_priced": f"Price for service {svc.name} must be exactly {svc.price}."})
            else:
                low = svc.price
                high = svc.price_up_to
                if price < low or price > high:
                    raise serializers.ValidationError({"services_priced": f"Price for service {svc.name} must be between {low} and {high}."})
            MedicalCardService.objects.update_or_create(
                medical_card=card,
                service=svc,
                defaults={"price": price},
            )
            selected_services.append(svc)
        return selected_services


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
            "amount",
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
    medical_card_id = serializers.PrimaryKeyRelatedField(
        source="medical_card", queryset=MedicalCard.objects.all(), write_only=True, required=False
    )
    medical_card = serializers.PrimaryKeyRelatedField(read_only=True)
    nurse = NurseSerializer(read_only=True)

    class Meta:
        model = Task
        fields = (
            "id",
            "schedule",
            "schedule_id",
            "nurse",
            "nurse_id",
            "medical_card",
            "medical_card_id",
            "description",
            "day",
            "due_time",
            "is_done",
            "done_at",
            "price",
        )
        read_only_fields = ("id", "done_at")

    def validate(self, attrs):
        schedule = attrs.get("schedule") or getattr(self.instance, "schedule", None)
        nurse = attrs.get("nurse") or getattr(self.instance, "nurse", None)
        day = attrs.get("day") or getattr(self.instance, "day", None)
        # Prevent marking done twice
        if getattr(self.instance, "is_done", False) and attrs.get("is_done") is True:
            raise serializers.ValidationError({"is_done": "Task is already marked as done."})
        # Nurse must be the schedule's assigned nurse
        if schedule and nurse and schedule.assigned_nurse_id != nurse.id:
            raise serializers.ValidationError({"nurse_id": "Nurse must match the schedule's assigned nurse."})
        # Task day must be within schedule date range
        if schedule and day and (day < schedule.start_date or day > schedule.end_date):
            raise serializers.ValidationError({"day": "Task day must be within the schedule date range."})
        return attrs


class DoctorTaskSerializer(serializers.ModelSerializer):
    """Serializer for DoctorTask with write-by-ID for relations.

    Price defaults from selected service if not provided.
    """

    doctor_id = serializers.PrimaryKeyRelatedField(
        source="doctor", queryset=DoctorSerializer.Meta.model.objects.all(), write_only=True
    )
    medical_card_id = serializers.PrimaryKeyRelatedField(
        source="medical_card", queryset=MedicalCard.objects.all(), write_only=True
    )
    service_id = serializers.PrimaryKeyRelatedField(
        source="service", queryset=Service.objects.all(), write_only=True
    )

    doctor = DoctorSerializer(read_only=True)
    medical_card = serializers.PrimaryKeyRelatedField(read_only=True)
    service = ServiceSerializer(read_only=True)

    class Meta:
        model = DoctorTask
        fields = (
            "id",
            "doctor",
            "doctor_id",
            "medical_card",
            "medical_card_id",
            "service",
            "service_id",
            "is_done",
            "done_at",
            "price",
            "created_at",
        )
        read_only_fields = ("id", "done_at", "created_at")

    def validate(self, attrs):
        card = attrs.get("medical_card") or getattr(self.instance, "medical_card", None)
        doc = attrs.get("doctor") or getattr(self.instance, "doctor", None)
        # Prevent double-done
        if getattr(self.instance, "is_done", False) and attrs.get("is_done") is True:
            raise serializers.ValidationError({"is_done": "Task is already marked as done."})
        if card and doc and card.doctor_id != doc.id:
            raise serializers.ValidationError({"doctor_id": "Doctor must match the medical card's doctor."})
        return attrs

    def create(self, validated_data):
        # Ensure price defaults from service
        svc = validated_data.get("service")
        if svc and (validated_data.get("price") in (None, 0, Decimal("0"))):
            validated_data["price"] = svc.price
        return super().create(validated_data)


class DoctorIncomeSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer(read_only=True)

    class Meta:
        model = DoctorIncome
        fields = ("doctor", "monthly_total", "last_reset")
        read_only_fields = fields


class NurseIncomeSerializer(serializers.ModelSerializer):
    nurse = NurseSerializer(read_only=True)

    class Meta:
        model = NurseIncome
        fields = ("nurse", "daily_total", "monthly_total", "last_reset")
        read_only_fields = fields


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


class MedicalUsageSerializer(serializers.Serializer):
    """Aggregated medicine usage per doctor.

    Represents how many times a doctor used a specific medicine across
    medical cards.
    """

    doctor_id = serializers.IntegerField()
    doctor_name = serializers.CharField()
    medicine_id = serializers.IntegerField()
    medicine_name = serializers.CharField()
    usage_count = serializers.IntegerField()


class PaymentSummaryItemSerializer(serializers.Serializer):
    """Represents a grouped revenue bucket (day/week/month)."""

    period = serializers.CharField(help_text="Grouping key: ISO date for day, week start date for week, YYYY-MM for month")
    total = serializers.DecimalField(max_digits=14, decimal_places=2)
    count = serializers.IntegerField()


class PaymentSummarySerializer(serializers.Serializer):
    """Revenue summary response schema."""

    total_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_count = serializers.IntegerField()
    items = PaymentSummaryItemSerializer(many=True)


class PaymentDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentDay
        fields = ("date", "price")
        read_only_fields = fields


class VisitSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(
        source="client", queryset=ClientSerializer.Meta.model.objects.all(), write_only=True
    )
    doctor = DoctorSerializer(read_only=True)
    doctor_id = serializers.PrimaryKeyRelatedField(
        source="doctor", queryset=DoctorSerializer.Meta.model.objects.all(), write_only=True
    )

    class Meta:
        model = Visit
        fields = ("id", "client", "client_id", "doctor", "doctor_id", "reason", "date", "created_at")
        read_only_fields = ("id", "created_at")
