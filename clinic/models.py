"""Clinic domain models for veterinary clinic management system.

This module defines Pets, Medicines, Services, MedicalCards, Payments,
StationaryRooms and their relationships with user profiles.
"""

# Standard library imports
from decimal import Decimal

# Django imports
from django.db import models
from django.db.models import Sum
from django.utils import timezone

# Project imports
from users.models import Admin, Client, Doctor, Nurse, Moderator


class GenderChoices(models.TextChoices):
    """Gender choices for pets."""

    MALE = "male", "Male"
    FEMALE = "female", "Female"


class Pet(models.Model):
    """A pet owned by a client.

    Each pet can be linked to multiple medical cards. A pet may optionally be
    assigned to a stationary room (via StationaryRoom.pet one-to-one field).
    """

    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="pets"
    )  # Owner of the pet
    name = models.CharField(max_length=255)
    breed = models.CharField(max_length=255, blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    gender = models.CharField(max_length=16, choices=GenderChoices.choices)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pet"
        verbose_name_plural = "Pets"
        ordering = ("name",)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.breed})"


class Medicine(models.Model):
    """Medicine available in the clinic inventory."""

    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    original_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, help_text="Purchase price for the clinic")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    expire_date = models.DateField()
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        Admin, on_delete=models.PROTECT, related_name="medicines"
    )  # Managed by admin

    class Meta:
        verbose_name = "Medicine"
        verbose_name_plural = "Medicines"
        ordering = ("name",)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} (qty: {self.quantity})"


class Service(models.Model):
    """Service offered by the clinic.

    Linked to nurse salary calculation via medical cards they are assigned to.
    """

    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        Admin, on_delete=models.PROTECT, related_name="services"
    )  # Managed by admin

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ("name",)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name}"


class MedicalCardStatus(models.TextChoices):
    """Status choices for medical cards."""

    PENDING = "pending", "Pending"
    IN_PROGRESS = "in_progress", "In Progress"
    PAID = "paid", "Paid"


class MedicalCard(models.Model):
    """A medical card recording treatments for a pet.

    Filled by a doctor; may be closed/paid by a moderator via Payment.
    """

    client = models.ForeignKey(
        Client, on_delete=models.PROTECT, related_name="medical_cards"
    )  # Patient's owner
    pet = models.ForeignKey(
        Pet, on_delete=models.PROTECT, related_name="medical_cards"
    )  # Patient pet
    doctor = models.ForeignKey(
        Doctor, on_delete=models.PROTECT, related_name="medical_cards"
    )  # Responsible doctor
    nurse = models.ForeignKey(
        Nurse, on_delete=models.SET_NULL, null=True, blank=True, related_name="medical_cards"
    )  # Assigned nurse (optional)
    # Optional stationary room assigned for in-patient treatment
    stationary_room = models.ForeignKey(
        'StationaryRoom', on_delete=models.SET_NULL, null=True, blank=True, related_name='medical_cards'
    )
    room_admission_date = models.DateTimeField(blank=True, null=True)
    room_release_date = models.DateTimeField(blank=True, null=True)

    services = models.ManyToManyField(
        Service, related_name="medical_cards", blank=True
    )  # Services rendered
    medicines = models.ManyToManyField(
        Medicine, related_name="medical_cards", blank=True
    )  # Medicines used

    status = models.CharField(max_length=16, choices=MedicalCardStatus.choices, default=MedicalCardStatus.PENDING)

    class general_conditions(models.TextChoices):
        HEALTHY = "healthy", "Healthy"
        SICK = "sick", "Sick"
        CRITICAL = "critical", "Critical"

    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    blood_pressure = models.CharField(max_length=50, blank=True, null=True)
    mucous_membrane = models.CharField(max_length=100, blank=True, null=True)
    heart_rate = models.PositiveIntegerField(blank=True, null=True)
    respiratory_rate = models.PositiveIntegerField(blank=True, null=True)
    general_condition = models.CharField(max_length=16, choices=general_conditions.choices, default=general_conditions.HEALTHY)
    chest_condition = models.TextField(blank=True, null=True)
    body_temperature = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    anamnesis = models.TextField(null=True, blank=True)
    diagnosis = models.TextField()
    diet = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    total_fee = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)

    revisit_date = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name = "Medical Card"
        verbose_name_plural = "Medical Cards"
        ordering = ("-created_at",)

    def __str__(self) -> str:  # pragma: no cover
        return f"MedicalCard #{self.pk} - {self.pet.name}"

    def update_total_fee(self) -> None:
        """Recalculate total fee from associated services and medicines."""
        service_total = sum((s.price for s in self.services.all()), start=Decimal("0"))
        medicine_total = sum((m.price for m in self.medicines.all()), start=Decimal("0"))
        self.total_fee = service_total + medicine_total
        # Don't call save(update_fields=[...]) here to avoid recursion in signals.
        super(MedicalCard, self).save(update_fields=["total_fee"])  # type: ignore[misc]

    def save(self, *args, **kwargs):
        # Set closed_at when status becomes PAID
        if self.status == MedicalCardStatus.PAID and self.closed_at is None:
            self.closed_at = timezone.now()
        elif self.status != MedicalCardStatus.PAID and self.closed_at is not None:
            # Reopen scenario
            self.closed_at = None
        super().save(*args, **kwargs)


class PaymentStatus(models.TextChoices):
    """Payment status choices."""

    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"


class PaymentMethod(models.TextChoices):
    """Payment method choices."""

    CASH = "cash", "Cash"
    CARD = "card", "Card"
    OTHER = "other", "Other"


class Payment(models.Model):
    """Payment record for a medical card closed by a moderator."""

    medical_card = models.OneToOneField(
        MedicalCard, on_delete=models.CASCADE, related_name="payment"
    )  # One payment per card
    status = models.CharField(max_length=16, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    method = models.CharField(max_length=16, choices=PaymentMethod.choices)
    processed_by = models.ForeignKey(
        Moderator, on_delete=models.PROTECT, related_name="processed_payments"
    )  # Processed by moderator
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ("-created_at",)

    def __str__(self) -> str:  # pragma: no cover
        return f"Payment for Card #{self.medical_card_id} - {self.status}"


class StationaryRoom(models.Model):
    """Stationary room to host a pet for in-patient treatment."""

    room_number = models.CharField(max_length=16, unique=True)
    is_occupied = models.BooleanField(default=False)
    pet = models.OneToOneField(
        Pet, on_delete=models.SET_NULL, related_name="stationary_room", blank=True, null=True
    )  # Pet occupying the room (optional)
    admission_date = models.DateTimeField(blank=True, null=True)
    release_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Stationary Room"
        verbose_name_plural = "Stationary Rooms"
        ordering = ("room_number",)

    def __str__(self) -> str:  # pragma: no cover
        occ = "occupied" if self.is_occupied else "free"
        return f"Room {self.room_number} ({occ})"

    def save(self, *args, **kwargs):
        # Keep is_occupied in sync with pet assignment and set admission/release dates.
        now = timezone.now()
        if self.pet and not self.is_occupied:
            # Assigning a pet to a free room
            self.is_occupied = True
            if not self.admission_date:
                self.admission_date = now
            # Preserve an explicitly set future release_date; clear only if invalid
            if self.release_date and self.admission_date and self.release_date < self.admission_date:
                self.release_date = None
        elif not self.pet and self.is_occupied:
            # Releasing the room
            self.is_occupied = False
            if not self.release_date:
                self.release_date = now
        super().save(*args, **kwargs)


# Signals to keep MedicalCard.total_fee in sync with many-to-many changes
from django.db.models.signals import m2m_changed
from django.dispatch import receiver


@receiver(m2m_changed, sender=MedicalCard.services.through)
@receiver(m2m_changed, sender=MedicalCard.medicines.through)
def update_total_fee_on_m2m_change(sender, instance: MedicalCard, action: str, **kwargs):
    """Recalculate total fee whenever services or medicines are modified."""
    if action in {"post_add", "post_remove", "post_clear"}:
        instance.update_total_fee()


# Keep MedicalCard status/closed_at in sync with payments
from django.db.models.signals import post_save


@receiver(post_save, sender=Payment)
def set_card_paid_on_payment(sender, instance: Payment, **kwargs):
    """When a payment is marked PAID, set the medical card to PAID and close it."""
    if instance.status == PaymentStatus.PAID:
        card = instance.medical_card
        if card.status != MedicalCardStatus.PAID:
            card.status = MedicalCardStatus.PAID
            # MedicalCard.save will populate closed_at when status is PAID
            card.save(update_fields=["status", "closed_at"])  # type: ignore[misc]


# =========================
# Nurse Management System
# =========================


class Schedule(models.Model):
    """Treatment plan created by a doctor for a specific medical card."""

    medical_card = models.ForeignKey(
        MedicalCard, on_delete=models.CASCADE, related_name="schedules"
    )
    created_by = models.ForeignKey(
        Doctor, on_delete=models.PROTECT, related_name="created_schedules"
    )
    assigned_nurse = models.ForeignKey(
        Nurse, on_delete=models.PROTECT, related_name="assigned_schedules"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Schedule"
        verbose_name_plural = "Schedules"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Schedule #{self.pk} for Card {self.medical_card_id}"


class Task(models.Model):
    """A nurse task belonging to a schedule."""

    schedule = models.ForeignKey(
        Schedule, on_delete=models.CASCADE, related_name="tasks"
    )
    nurse = models.ForeignKey(
        Nurse, on_delete=models.PROTECT, related_name="tasks"
    )
    description = models.TextField()
    day = models.DateField()
    due_time = models.TimeField()
    is_done = models.BooleanField(default=False)
    done_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ("day", "due_time")

    def __str__(self) -> str:
        return f"Task #{self.pk} - Nurse {self.nurse_id} on {self.day}"


class NurseDailySalary(models.Model):
    """Daily earnings and task statistics for a nurse."""

    nurse = models.ForeignKey(
        Nurse, on_delete=models.CASCADE, related_name="daily_salaries"
    )
    date = models.DateField(auto_now_add=True)
    total_tasks = models.PositiveIntegerField(default=0)
    completed_tasks = models.PositiveIntegerField(default=0)
    salary = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))

    class Meta:
        verbose_name = "Nurse Daily Salary"
        verbose_name_plural = "Nurse Daily Salaries"
        unique_together = ("nurse", "date")
        ordering = ("-date",)

    def __str__(self) -> str:
        return f"{self.nurse_id} - {self.date}: {self.salary}"


# Signals for Task completion and salary updates
from django.db.models.signals import pre_save, post_save, post_delete


def _recalculate_daily_salary(nurse: Nurse, the_day) -> None:
    """Recalculate stats and salary for a nurse on a specific day."""
    qs = Task.objects.filter(nurse=nurse, day=the_day)
    total = qs.count()
    completed = qs.filter(is_done=True).count()
    rate = nurse.rate_per_task or Decimal("0")
    salary_amount = (rate * Decimal(completed)) if completed else Decimal("0")
    obj, _created = NurseDailySalary.objects.get_or_create(
        nurse=nurse,
        date=the_day,
        defaults={
            "total_tasks": total,
            "completed_tasks": completed,
            "salary": salary_amount,
        },
    )
    if not _created:
        obj.total_tasks = total
        obj.completed_tasks = completed
        obj.salary = salary_amount
        obj.save(update_fields=["total_tasks", "completed_tasks", "salary"])

    # Update nurse aggregates: today's salary_per_day and overall total_salary
    today = timezone.localdate()
    update_fields = []
    if the_day == today:
        nurse.salary_per_day = obj.salary
        update_fields.append("salary_per_day")
    # total_salary = sum of all daily salaries
    agg = NurseDailySalary.objects.filter(nurse=nurse).aggregate(total=Sum("salary"))
    nurse.total_salary = agg.get("total") or Decimal("0")
    update_fields.append("total_salary")
    nurse.save(update_fields=update_fields)


@receiver(pre_save, sender=Task)
def set_done_at_on_completion(sender, instance: Task, **kwargs):
    """Automatically set done_at when a task transitions to done."""
    if not instance.pk:
        # New task; nothing to compare
        if instance.is_done and not instance.done_at:
            instance.done_at = timezone.now()
        return
    try:
        prev = Task.objects.get(pk=instance.pk)
    except Task.DoesNotExist:
        prev = None
    if instance.is_done and (not prev or not prev.is_done) and not instance.done_at:
        instance.done_at = timezone.now()


@receiver(post_save, sender=Task)
def update_salary_on_task_save(sender, instance: Task, **kwargs):
    _recalculate_daily_salary(instance.nurse, instance.day)


@receiver(post_delete, sender=Task)
def update_salary_on_task_delete(sender, instance: Task, **kwargs):
    _recalculate_daily_salary(instance.nurse, instance.day)
