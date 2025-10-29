from __future__ import annotations

import asyncio
from django.core.management.base import BaseCommand
from django.conf import settings

from telegram_bot.bot import get_dispatcher_and_bot


class Command(BaseCommand):
    help = "Set or delete Telegram webhook based on TELEGRAM_WEBHOOK_URL"

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["set", "delete"], help="Set or delete webhook")

    def handle(self, *args, **options):
        action = options["action"]
        dp, bot = get_dispatcher_and_bot()

        async def main():
            if action == "delete":
                await bot.delete_webhook(drop_pending_updates=True)
                self.stdout.write(self.style.SUCCESS("Webhook deleted"))
            else:
                url = getattr(settings, "TELEGRAM_WEBHOOK_URL", None)
                if not url:
                    self.stderr.write("TELEGRAM_WEBHOOK_URL not configured")
                    return
                await bot.set_webhook(url=url, drop_pending_updates=True)
                self.stdout.write(self.style.SUCCESS(f"Webhook set to {url}"))

        asyncio.run(main())
