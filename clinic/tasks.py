"""Celery tasks for clinic domain scheduled operations.

Includes:
- release_due_rooms: releases rooms automatically when release_date passes
- reset_daily_nurse_salary: resets nurses' per-day salary at midnight
"""

from celery import shared_task
from django.utils import timezone

from .models import StationaryRoom, MedicalCard
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
