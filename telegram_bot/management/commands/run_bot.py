from __future__ import annotations

import asyncio
from django.core.management.base import BaseCommand
from django.conf import settings

from aiogram.types import BotCommand

from telegram_bot.bot import get_dispatcher_and_bot


class Command(BaseCommand):
    help = "Run Telegram bot in polling mode"

    def handle(self, *args, **options):
        dp, bot = get_dispatcher_and_bot()

        async def main():
            await bot.set_my_commands(
                [
                    BotCommand(command="start", description="Start the bot"),
                    BotCommand(command="announce", description="Send broadcast (admins/mods)"),
                ]
            )
            await dp.start_polling(bot)

        asyncio.run(main())
