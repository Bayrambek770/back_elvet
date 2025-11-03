"""Celery tasks for clinic domain scheduled operations.

Includes:
- release_due_rooms: releases rooms automatically when release_date passes
- reset_daily_nurse_salary: resets nurses' per-day salary at midnight
"""

from celery import shared_task
from django.utils import timezone

from .models import StationaryRoom, MedicalCard, DoctorIncome, NurseIncome, PaymentDay
from users.models import Nurse
import logging


@shared_task
def release_due_rooms() -> int:
    """Release rooms whose release_date has passed.

    Returns the count of rooms released.
    """
    now = timezone.now()
    to_release = StationaryRoom.objects.filter(
        release_date__isnull=False,
        release_date__lte=now,
        pet__isnull=False,
    )
    count = 0
    for room in to_release:
        room.pet = None
        room.save()
        count += 1
    return count


@shared_task
def reset_daily_nurse_salary() -> int:
    """Reset salary_per_day for all nurses to 0 at the start of a new day.

    Returns number of nurses updated.
    """
    updated = Nurse.objects.update(salary_per_day=0)
    return updated


@shared_task
def nurse_income_daily_rollover() -> int:
    """Roll daily totals into monthly totals and reset daily_total to 0.

    Returns number of nurse income records updated and logs the operation time.
    """
    logger = logging.getLogger(__name__)
    now = timezone.now()
    count = 0
    for inc in NurseIncome.objects.all():
        inc.monthly_total = (inc.monthly_total or 0) + (inc.daily_total or 0)
        inc.daily_total = 0
        inc.last_reset = now
        inc.save(update_fields=["monthly_total", "daily_total", "last_reset"])  # type: ignore[misc]
        count += 1
    logger.info("Nurse income rollover executed at %s for %d records", now.isoformat(), count)
    return count


@shared_task
def reset_doctor_monthly_income() -> int:
    """Reset doctor monthly totals at month start; run daily around midnight.

    Returns number of doctor income records reset. If not first day of month, does nothing.
    """
    now = timezone.localdate()
    # Only reset on first day of each month
    if now.day != 1:
        return 0
    ts = timezone.now()
    count = 0
    for inc in DoctorIncome.objects.all():
        inc.monthly_total = 0
        inc.last_reset = ts
        inc.save(update_fields=["monthly_total", "last_reset"])  # type: ignore[misc]
        count += 1
    return count


@shared_task
def ensure_payment_day_exists() -> int:
    """Ensure a PaymentDay record exists for today with default price=0.

    Returns 1 if created, 0 if already existed.
    """
    today = timezone.localdate()
    _obj, created = PaymentDay.objects.get_or_create(date=today, defaults={"price": 0})
    return 1 if created else 0


@shared_task
def send_revisit_reminders() -> int:
    """Send reminders 2 days and 1 day before a medical card's revisit_date.

    Returns the number of reminders processed.
    """
    logger = logging.getLogger(__name__)
    today = timezone.localdate()
    targets = MedicalCard.objects.filter(revisit_date__in=[today + timezone.timedelta(days=1), today + timezone.timedelta(days=2)])
    count = 0
    for card in targets.select_related("client__user", "pet"):
        client_user = getattr(card.client, "user", None)
        phone = getattr(client_user, "phone_number", None)
        pet_name = getattr(card.pet, "name", "pet")
        days_left = (card.revisit_date - today).days if card.revisit_date else None
        msg = f"Reminder: {days_left} day(s) left until revisit for {pet_name} on {card.revisit_date}."
        # Placeholder notification: log (integrate SMS/Email provider here)
        logger.info("Sending revisit reminder to %s: %s", phone or "<no-phone>", msg)
        count += 1
    return count
