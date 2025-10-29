from __future__ import annotations

from django.urls import path
from .views import telegram_webhook

urlpatterns = [
    path("webhook/telegram/", telegram_webhook, name="telegram_webhook"),
]
