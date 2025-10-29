from __future__ import annotations

from django.conf import settings
from asgiref.sync import sync_to_async

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from telegram_bot.utils import is_admin_or_moderator
from telegram_bot.i18n import t, DEFAULT_LANG
from telegram_bot.models import TelegramAnnouncement
from telegram_bot.tasks import send_announcement_broadcast

admin_router = Router(name="admin")


@admin_router.message(Command("announce"))
async def announce(message: Message):
    """Broadcast a message to all verified clients. Only admins/moderators."""
    user_id = message.from_user.id
    if not await sync_to_async(is_admin_or_moderator)(user_id):
        await message.reply(t("not_allowed", DEFAULT_LANG))
        return

    # Extract text after command
    text = message.text or ""
    parts = text.split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        await message.reply(t("announce_usage", DEFAULT_LANG))
        return
    content = parts[1].strip()

    # Create announcement log and trigger celery broadcast
    # Map telegram_id -> user for sent_by; if multiple, pick the first match
    from users.models import Client

    async def _create_announcement():
        cli = await sync_to_async(
            lambda: Client.objects.filter(telegram_id=user_id).select_related("user").first()
        )()
        sender = cli.user if cli else None
        ann = await sync_to_async(TelegramAnnouncement.objects.create)(
            title="Bot /announce", message=content, sent_by=sender
        )
        return ann

    ann = await _create_announcement()
    send_announcement_broadcast.delay(ann.id)

    await message.reply(t("broadcast_started", DEFAULT_LANG))
