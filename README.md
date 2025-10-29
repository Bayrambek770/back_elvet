# back_elvet
Veterinary clinic management API with JWT auth, DRF, Celery, and Telegram Bot integration.

## Telegram Bot

The `telegram_bot` app provides client onboarding and admin announcements using aiogram 3.x.

Environment variables (in `.env`):

- `TELEGRAM_BOT_TOKEN` — Telegram bot token
- `TELEGRAM_MODE` — `polling` or `webhook` (default: `polling`)
- `TELEGRAM_WEBHOOK_URL` — Public HTTPS URL for webhook mode
- `TELEGRAM_LOGIN_URL_BASE` — Frontend login URL base used by the bot to send login links

Run in polling mode:

```bash
python manage.py run_bot
```

Webhook mode:

```bash
# Set webhook to the public URL
python manage.py set_telegram_webhook set

# To delete webhook
python manage.py set_telegram_webhook delete
```

Webhook endpoint will be available at `/bot/webhook/telegram/`.

Broadcast announcements:

- From Django Admin: add a Telegram Announcement and use the admin action “Broadcast selected announcements again” to send/resend.
- From bot (admins/moderators only): `/announce Your message here`

Client onboarding flow via bot:

1. `/start` → share phone number
2. Enter first and last name
3. Set a password (min 6 chars)
4. Bot registers user as Client, links Telegram, and returns a login link

