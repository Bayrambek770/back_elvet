from __future__ import annotations

import asyncio
import logging
from typing import Iterable

from celery import shared_task
from django.conf import settings
from django.db.models import Q

from aiogram import Bot

from users.models import Client, RoleChoices, User
from .models import TelegramAnnouncement

logger = logging.getLogger(__name__)


async def _broadcast_async(bot: Bot, user_ids: Iterable[int], text: str, throttle: float = 0.05) -> int:
    """Send a message to many users with throttling to avoid rate limits.

    Returns the number of successful sends.
    """
    sent = 0
    for uid in user_ids:
        try:
            await bot.send_message(chat_id=uid, text=text)
            sent += 1
        except Exception as e:  # pragma: no cover - network/runtime dependent
            logger.warning("Failed to send to %s: %s", uid, e)
        await asyncio.sleep(throttle)
    return sent


@shared_task
def send_announcement_broadcast(announcement_id: int) -> int:
    """Celery task to broadcast an announcement to all verified clients.

    Returns number of successful deliveries.
    """
    ann = TelegramAnnouncement.objects.get(id=announcement_id)

    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is not configured")
        return 0

    # Collect target user IDs from Client.verified and telegram_id present.
    clients = Client.objects.filter(is_verified_via_telegram=True).exclude(telegram_id__isnull=True)
    user_ids = list(clients.values_list("telegram_id", flat=True))

    async def runner() -> int:
        bot = Bot(token=bot_token)
        try:
            return await _broadcast_async(bot, user_ids=user_ids, text=ann.message)
        finally:
            await bot.session.close()

    sent = asyncio.run(runner())
    TelegramAnnouncement.objects.filter(pk=ann.pk).update(target_count=sent)
    return sent
