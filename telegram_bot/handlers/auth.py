from __future__ import annotations

import re
from typing import Optional

from django.conf import settings
from django.db import transaction
from asgiref.sync import sync_to_async
from django.utils import timezone

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User, RoleChoices, Client
from telegram_bot.utils import normalize_phone
from telegram_bot.i18n import t, LANG_BUTTONS, DEFAULT_LANG


auth_router = Router(name="auth")


class AuthStates(StatesGroup):
    waiting_for_language = State()
    waiting_for_contact = State()
    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_password = State()


@auth_router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    # Ask to choose language first
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=LANG_BUTTONS["en"]), KeyboardButton(text=LANG_BUTTONS["ru"]), KeyboardButton(text=LANG_BUTTONS["uz"])]],
        resize_keyboard=True,
    )
    await state.set_state(AuthStates.waiting_for_language)
    await message.answer(t("choose_language", DEFAULT_LANG), reply_markup=kb)


@auth_router.message(AuthStates.waiting_for_language)
async def got_language(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    # Map typed button back to code
    lang_code = None
    for code, label in LANG_BUTTONS.items():
        if text.lower() == label.lower():
            lang_code = code
            break
    if not lang_code:
        # Repeat prompt
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=LANG_BUTTONS["en"]), KeyboardButton(text=LANG_BUTTONS["ru"]), KeyboardButton(text=LANG_BUTTONS["uz"])]],
            resize_keyboard=True,
        )
        await message.answer(t("choose_language", DEFAULT_LANG), reply_markup=kb)
        return
    await state.update_data(lang=lang_code)
    # Proceed to ask for contact with localized button
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("btn_share_phone", lang_code), request_contact=True)]], resize_keyboard=True
    )
    await state.set_state(AuthStates.waiting_for_contact)
    await message.answer(t("share_phone", lang_code), reply_markup=kb)


@auth_router.message(AuthStates.waiting_for_contact, F.contact)
async def got_contact(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", DEFAULT_LANG)
    if not message.contact or not message.contact.phone_number:
        await message.answer(t("invalid_phone", lang))
        return
    phone = normalize_phone(message.contact.phone_number)
    await state.update_data(phone=phone, telegram_id=message.from_user.id)

    # Check if user exists
    user = await sync_to_async(User.objects.filter(phone_number=phone).first)()
    if user:
        # Link Telegram for clients, but do not continue onboarding
        if user.role == RoleChoices.CLIENT:
            await sync_to_async(Client.objects.filter(user=user).update)(
                telegram_id=message.from_user.id,
                is_verified_via_telegram=True,
                language=lang,
            )
        await message.answer(t("already_registered", lang), reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    # Ask for first name
    await state.set_state(AuthStates.waiting_for_first_name)
    await message.answer(t("ask_first_name", lang), reply_markup=ReplyKeyboardRemove())


@auth_router.message(AuthStates.waiting_for_first_name)
async def got_first_name(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", DEFAULT_LANG)
    if not message.text or not message.text.replace(" ", "").isalpha():
        await message.answer(t("invalid_first_name", lang))
        return
    await state.update_data(first_name=message.text.strip())
    await state.set_state(AuthStates.waiting_for_last_name)
    await message.answer(t("ask_last_name", lang))


@auth_router.message(AuthStates.waiting_for_last_name)
async def got_last_name(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", DEFAULT_LANG)
    if not message.text or not message.text.replace(" ", "").isalpha():
        await message.answer(t("invalid_last_name", lang))
        return
    await state.update_data(last_name=message.text.strip())
    await state.set_state(AuthStates.waiting_for_password)
    await message.answer(t("ask_password", lang))


@auth_router.message(AuthStates.waiting_for_password)
async def got_password(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", DEFAULT_LANG)
    if not message.text or len(message.text) < 6:
        await message.answer(t("invalid_password", lang))
        return
    phone = data.get("phone")
    telegram_id = data.get("telegram_id")
    first_name = data.get("first_name")
    last_name = data.get("last_name")

    # Create user atomically inside a sync context, called from async
    def _create_or_link_user() -> User:
        with transaction.atomic():
            user = User.objects.filter(phone_number=phone).first()
            if not user:
                user = User.objects.create_user(
                    phone_number=phone,
                    password=message.text,
                    role=RoleChoices.CLIENT,
                    first_name=first_name,
                    last_name=last_name,
                )
            else:
                # Ensure role is client for onboarding path; update profile data from user input
                if user.role != RoleChoices.CLIENT:
                    raise ValueError("User role not client")
                user.first_name = first_name or user.first_name
                user.last_name = last_name or user.last_name
                if message.text:
                    user.set_password(message.text)
                user.save(update_fields=["first_name", "last_name", "password"])

            client = Client.objects.filter(user=user).first()
            if not client:
                client = Client.objects.create(user=user)
            client.telegram_id = telegram_id
            client.is_verified_via_telegram = True
            # Persist chosen language for future bot interactions
            try:
                if lang in {"en", "ru", "uz"}:
                    client.language = lang
            except Exception:
                pass
            client.save(update_fields=["telegram_id", "is_verified_via_telegram", "language"])
            return user

    user: User = await sync_to_async(_create_or_link_user)()

    # Final confirmation without sending login link (localized)
    await message.answer(t("registered_notice", lang))
    await state.clear()
