from __future__ import annotations

import json
import logging
from django.conf import settings
from django.http import HttpRequest, JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from aiogram.types import Update

from .bot import get_dispatcher_and_bot

logger = logging.getLogger(__name__)


@csrf_exempt
async def telegram_webhook(request: HttpRequest):
    """Async webhook endpoint to receive Telegram updates.

    Feeds updates to aiogram Dispatcher.
    """
    if request.method != "POST":
        return HttpResponse(status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return HttpResponse(status=400)

    dispatcher, bot = get_dispatcher_and_bot()
    try:
        update = Update.model_validate(data)
        await dispatcher.feed_update(bot=bot, update=update)
        return JsonResponse({"ok": True})
    except Exception as e:  # pragma: no cover - runtime dependent
        logger.exception("Webhook handling failed: %s", e)
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
