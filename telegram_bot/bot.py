from __future__ import annotations

import logging
from typing import Tuple

from django.conf import settings

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from .handlers.auth import auth_router
from .handlers.admin import admin_router

logger = logging.getLogger(__name__)

_bot: Bot | None = None
_dp: Dispatcher | None = None


def get_dispatcher_and_bot() -> Tuple[Dispatcher, Bot]:
    global _bot, _dp
    if _bot is None:
        token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
        _bot = Bot(token=token)
    if _dp is None:
        _dp = Dispatcher(storage=MemoryStorage())
        _dp.include_router(auth_router)
        _dp.include_router(admin_router)
    return _dp, _bot  # type: ignore[return-value]
