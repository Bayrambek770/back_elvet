from __future__ import annotations

from typing import Literal

Lang = Literal["en", "ru", "uz"]

LANG_BUTTONS = {
    "en": "English",
    "ru": "Русский",
    "uz": "O'zbekcha",
}

DEFAULT_LANG: Lang = "en"

_MESSAGES: dict[Lang, dict[str, str]] = {
    "en": {
        "choose_language": "Please choose your language:",
        "btn_share_phone": "Share phone number",
        "share_phone": "Welcome to the Clinic! Please share your phone number to continue.",
        "invalid_phone": "❌ Invalid phone number format. Please share it using the button.",
        "clients_only": "❌ Telegram login is available for clients only.",
        "ask_first_name": "Please enter your first name:",
        "invalid_first_name": "❌ First name must contain only letters. Try again:",
        "ask_last_name": "Enter your last name:",
        "invalid_last_name": "❌ Last name must contain only letters. Try again:",
        "ask_password": "Create a password (min 6 chars):",
        "invalid_password": "❌ Password too short. Enter at least 6 characters:",
        "already_registered": "✅ You are already registered. You can login at the site using your credentials.",
        "registered_success": "✅ Registered successfully!",
        "login_link": "🔗 Login Link: ",
        "registered_notice": "You are successfully registered and now you can log in in our website: elvet.uz",
        "not_allowed": "❌ You are not allowed to use this command.",
        "announce_usage": "Usage: /announce Your message here",
        "broadcast_started": "📣 Broadcast started.",
    },
    "ru": {
        "choose_language": "Пожалуйста, выберите язык:",
        "btn_share_phone": "Поделиться номером телефона",
        "share_phone": "Добро пожаловать в клинику! Пожалуйста, поделитесь номером телефона для продолжения.",
        "invalid_phone": "❌ Неверный формат номера. Пожалуйста, используйте кнопку для отправки контакта.",
        "clients_only": "❌ Вход через Telegram доступен только для клиентов.",
        "ask_first_name": "Введите ваше имя:",
        "invalid_first_name": "❌ Имя должно содержать только буквы. Попробуйте ещё раз:",
        "ask_last_name": "Введите вашу фамилию:",
        "invalid_last_name": "❌ Фамилия должна содержать только буквы. Попробуйте ещё раз:",
        "ask_password": "Создайте пароль (не менее 6 символов):",
        "invalid_password": "❌ Слишком короткий пароль. Введите минимум 6 символов:",
        "already_registered": "✅ Вы уже зарегистрированы. Вы можете войти на сайт, используя свои данные.",
        "registered_success": "✅ Регистрация прошла успешно!",
        "login_link": "🔗 Ссылка для входа: ",
        "registered_notice": "Вы успешно зарегистрированы и теперь можете войти на наш сайт: elvet.uz",
        "not_allowed": "❌ У вас нет прав для этой команды.",
        "announce_usage": "Использование: /announce Ваше сообщение",
        "broadcast_started": "📣 Рассылка запущена.",
    },
    "uz": {
        "choose_language": "Iltimos, tilni tanlang:",
        "btn_share_phone": "Telefon raqamni ulashish",
        "share_phone": "Klinikamizga xush kelibsiz! Davom etish uchun telefon raqamingizni ulashing.",
        "invalid_phone": "❌ Telefon raqami noto'g'ri. Iltimos, tugma orqali yuboring.",
        "clients_only": "❌ Telegram orqali kirish faqat mijozlar uchun mavjud.",
        "ask_first_name": "Ismingizni kiriting:",
        "invalid_first_name": "❌ Ism faqat harflardan iborat bo'lishi kerak. Qayta urinib ko'ring:",
        "ask_last_name": "Familiyangizni kiriting:",
        "invalid_last_name": "❌ Familiya faqat harflardan iborat bo'lishi kerak. Qayta urinib ko'ring:",
        "ask_password": "Parol yarating (kamida 6 ta belgi):",
        "invalid_password": "❌ Parol juda qisqa. Kamida 6 ta belgi kiriting:",
        "already_registered": "✅ Siz allaqachon ro'yxatdan o'tgansiz. Sayt orqali kirish mumkin.",
        "registered_success": "✅ Muvaffaqiyatli ro'yxatdan o'tdingiz!",
        "login_link": "🔗 Kirish havolasi: ",
        "registered_notice": "Siz muvaffaqiyatli ro'yxatdan o'tdingiz va endi bizning saytimizga kirishingiz mumkin: elvet.uz",
        "not_allowed": "❌ Bu buyruqdan foydalanishga ruxsatingiz yo'q.",
        "announce_usage": "Foydalanish: /announce Xabaringiz",
        "broadcast_started": "📣 Tarqatish boshlandi.",
    },
}


def t(key: str, lang: str | None) -> str:
    code: Lang = (lang or DEFAULT_LANG) if (lang or DEFAULT_LANG) in _MESSAGES else DEFAULT_LANG
    return _MESSAGES[code].get(key, key)
