"""Clinic domain models for veterinary clinic management system.

This module defines Pets, Medicines, Services, MedicalCards, Payments,
StationaryRooms and their relationships with user profiles.
"""

# Standard library imports
from decimal import Decimal

# Django imports
from django.db import models, transaction
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
    
    class AnimalTypeChoices(models.TextChoices):
        DOG = "dog", "Dog"
        CAT = "cat", "Cat"
        BIRD = "bird", "Bird"
        REPTILE = "reptile", "Reptile"
        RODENT = "rodent", "Rodent"
        OTHER = "other", "Other"

    animal_type = models.CharField(max_length=16, choices=AnimalTypeChoices.choices, default=AnimalTypeChoices.OTHER)
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
    price_up_to = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Optional upper bound for variable pricing"
    )
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
    )  # Services rendered; variable prices stored in MedicalCardService
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
        # Sum selected prices from MedicalCardService when available; otherwise fallback to M2M services' base prices
        links = list(self.service_links.all())
        if links:
            service_total = sum((ms.price for ms in links), start=Decimal("0"))
        else:
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
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
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


class PaymentDay(models.Model):
    """Aggregated payments per calendar day.

    Keeps a single row per day with the total income captured that day.
    If no payments occur on a day, a row can exist with price=0 for reporting.
    """

    date = models.DateField(unique=True)
    price = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Payment Day"
        verbose_name_plural = "Payment Days"
        ordering = ("-date",)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.date}: {self.price}"


class Visit(models.Model):
    """A client visit to the clinic for a specific doctor.

    Captures which client came, to which doctor, optional reason, and the visit date.
    """

    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="visits")
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, related_name="visits")
    reason = models.TextField(blank=True, null=True)
    date = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Visit"
        verbose_name_plural = "Visits"
        ordering = ("-date", "-created_at")

    def __str__(self) -> str:  # pragma: no cover
        return f"Visit: client {self.client_id} -> doctor {self.doctor_id} on {self.date}"


class MedicalCardService(models.Model):
    """Selected service for a medical card with the chosen price.

    If Service.price_up_to is not set, price should equal Service.price.
    """

    medical_card = models.ForeignKey(MedicalCard, on_delete=models.CASCADE, related_name="service_links")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name="card_links")
    price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Medical Card Service"
        verbose_name_plural = "Medical Card Services"
        unique_together = ("medical_card", "service")

    def __str__(self) -> str:  # pragma: no cover
        return f"Card {self.medical_card_id} - {self.service_id}: {self.price}"


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


@receiver(m2m_changed, sender=MedicalCard.medicines.through)
def update_total_fee_on_m2m_change(sender, instance: MedicalCard, action: str, **kwargs):
    """Recalculate total fee whenever services or medicines are modified."""
    if action in {"post_add", "post_remove", "post_clear"}:
        instance.update_total_fee()


# Keep MedicalCard status/closed_at in sync with payments
from django.db.models.signals import post_save, post_delete, pre_save
from django.db.models import F


@receiver(post_save, sender=Payment)
def set_card_paid_on_payment(sender, instance: Payment, **kwargs):
    """When a payment is marked PAID, set the medical card to PAID and close it."""
    if instance.status == PaymentStatus.PAID:
        # Ensure amount is recorded; default to medical card's total_fee if not provided
        if instance.amount is None or instance.amount == 0:
            try:
                Payment.objects.filter(pk=instance.pk).update(amount=instance.medical_card.total_fee)
            except Exception:
                pass
        card = instance.medical_card
        if card.status != MedicalCardStatus.PAID:
            card.status = MedicalCardStatus.PAID
            # MedicalCard.save will populate closed_at when status is PAID
            card.save(update_fields=["status", "closed_at"])  # type: ignore[misc]


# Track transitions to PAID to update PaymentDay totals
@receiver(pre_save, sender=Payment)
def mark_payment_transition(sender, instance: Payment, **kwargs):
    if not instance.pk:
        # New object; mark if created as PAID
        instance._became_paid = (instance.status == PaymentStatus.PAID)
        return
    try:
        prev = Payment.objects.get(pk=instance.pk)
    except Payment.DoesNotExist:
        prev = None
    instance._became_paid = bool(prev and prev.status != PaymentStatus.PAID and instance.status == PaymentStatus.PAID)


@receiver(post_save, sender=Payment)
def update_payment_day_on_paid(sender, instance: Payment, created: bool, **kwargs):
    became_paid = bool(getattr(instance, "_became_paid", False) or (created and instance.status == PaymentStatus.PAID))
    if not became_paid:
        return
    # Determine effective amount, fallback to card.total_fee if zero
    amount = instance.amount or instance.medical_card.total_fee
    if not amount:
        return
    day = timezone.localdate()
    obj, _ = PaymentDay.objects.get_or_create(date=day, defaults={"price": Decimal("0")})
    # Atomic increment
    PaymentDay.objects.filter(pk=obj.pk).update(price=F("price") + amount)


# Keep total fee in sync when service selections change (through model updates)
@receiver(post_save, sender=MedicalCardService)
def update_total_fee_on_service_link_save(sender, instance: MedicalCardService, **kwargs):
    instance.medical_card.update_total_fee()


@receiver(post_delete, sender=MedicalCardService)
def update_total_fee_on_service_link_delete(sender, instance: MedicalCardService, **kwargs):
    instance.medical_card.update_total_fee()


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
    # Direct link for traceability; defaults to schedule.medical_card at creation time
    medical_card = models.ForeignKey(
        MedicalCard, on_delete=models.PROTECT, related_name="nurse_tasks", null=True, blank=True
    )
    description = models.TextField()
    day = models.DateField()
    due_time = models.TimeField()
    is_done = models.BooleanField(default=False)
    done_at = models.DateTimeField(blank=True, null=True)
    # Per-task price; if not provided, may default from nurse.rate_per_task
    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))

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
        # Ensure medical_card is set to the schedule's medical_card if missing
        if instance.schedule and not instance.medical_card:
            instance.medical_card = instance.schedule.medical_card
        # Default price from nurse.rate_per_task if not provided
        if (instance.price is None or instance.price == Decimal("0")) and getattr(instance.nurse, "rate_per_task", None):
            instance.price = instance.nurse.rate_per_task
        # Mark transition for post_save handler
        instance._mark_done_transition = bool(instance.is_done)
        return
    try:
        prev = Task.objects.get(pk=instance.pk)
    except Task.DoesNotExist:
        prev = None
    if instance.is_done and (not prev or not prev.is_done) and not instance.done_at:
        instance.done_at = timezone.now()
    # Mark transition for post_save handler
    instance._mark_done_transition = bool((prev and not prev.is_done) and instance.is_done)


@receiver(post_save, sender=Task)
def update_salary_on_task_save(sender, instance: Task, **kwargs):
    _recalculate_daily_salary(instance.nurse, instance.day)


@receiver(post_delete, sender=Task)
def update_salary_on_task_delete(sender, instance: Task, **kwargs):
    _recalculate_daily_salary(instance.nurse, instance.day)


# =========================
# Doctor Tasks & Incomes
# =========================


class DoctorIncome(models.Model):
    """Tracks a doctor's monthly income accumulated from completed doctor tasks."""

    doctor = models.OneToOneField(Doctor, on_delete=models.CASCADE, related_name="income")
    monthly_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    last_reset = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Doctor Income"
        verbose_name_plural = "Doctor Incomes"

    def __str__(self) -> str:  # pragma: no cover
        return f"DoctorIncome {self.doctor_id}: {self.monthly_total}"


class DoctorTask(models.Model):
    """A doctor's task linked to a medical service and card.

    Price is captured from the service at creation time. When marked done,
    the price contributes 100% to the doctor's monthly income.
    """

    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, related_name="tasks")
    medical_card = models.ForeignKey(MedicalCard, on_delete=models.PROTECT, related_name="doctor_tasks")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name="doctor_tasks")
    is_done = models.BooleanField(default=False)
    done_at = models.DateTimeField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Doctor Task"
        verbose_name_plural = "Doctor Tasks"
        ordering = ("-created_at",)

    def __str__(self) -> str:  # pragma: no cover
        return f"DoctorTask #{self.pk} - Doctor {self.doctor_id}"


# Signals for doctor task transitions and nurse income updates


@receiver(pre_save, sender=DoctorTask)
def set_doctor_task_defaults(sender, instance: "DoctorTask", **kwargs):
    """Ensure price and done_at are set appropriately on creation/updates."""
    if not instance.pk:
        # Default price from service
        if instance.service and (instance.price is None or instance.price == Decimal("0")):
            instance.price = instance.service.price
        if instance.is_done and not instance.done_at:
            instance.done_at = timezone.now()
        return
    try:
        prev = DoctorTask.objects.get(pk=instance.pk)
    except DoctorTask.DoesNotExist:
        prev = None
    if instance.is_done and (not prev or not prev.is_done) and not instance.done_at:
        instance.done_at = timezone.now()


@receiver(post_save, sender=DoctorTask)
def increment_doctor_income_on_done(sender, instance: "DoctorTask", created: bool, **kwargs):
    """When a doctor task transitions to done, increment monthly income by price."""
    transitioned = bool(getattr(instance, "_mark_done_transition", False) or (created and instance.is_done))
    if not transitioned:
        return
    with transaction.atomic():
        income, _ = DoctorIncome.objects.select_for_update().get_or_create(doctor=instance.doctor)
        income.monthly_total = (income.monthly_total or Decimal("0")) + (instance.price or Decimal("0"))
        income.save(update_fields=["monthly_total"])  # type: ignore[misc]


# =========================
# Nurse Incomes
# =========================


class NurseIncome(models.Model):
    """Tracks nurse daily and monthly incomes based on completed tasks."""

    nurse = models.OneToOneField(Nurse, on_delete=models.CASCADE, related_name="income")
    daily_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    monthly_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    last_reset = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Nurse Income"
        verbose_name_plural = "Nurse Incomes"

    def __str__(self) -> str:  # pragma: no cover
        return f"NurseIncome {self.nurse_id}: D={self.daily_total} M={self.monthly_total}"


@receiver(post_save, sender=Task)
def increment_nurse_income_on_task_done(sender, instance: Task, created: bool, **kwargs):
    """When a nurse task transitions to done, increment NurseIncome.daily_total by price."""
    transitioned = bool(getattr(instance, "_mark_done_transition", False) or (created and instance.is_done))
    if not transitioned:
        return
    with transaction.atomic():
        inc, _ = NurseIncome.objects.select_for_update().get_or_create(nurse=instance.nurse)
        inc.daily_total = (inc.daily_total or Decimal("0")) + (instance.price or Decimal("0"))
        inc.save(update_fields=["daily_total"])  # type: ignore[misc]
