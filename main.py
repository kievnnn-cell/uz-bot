import os
import telebot
from telebot import types

# ======================
# TOKEN (берём из ENV Render)
# ======================
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise Exception("BOT_TOKEN is not set in environment variables")

bot = telebot.TeleBot(TOKEN)

# ======================
# STATE STORAGE (простое FSM без баз данных)
# ======================
user_state = {}

STATE_START = "start"
STATE_WAIT_ROUTE = "wait_route"


# ======================
# START
# ======================
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    user_state[user_id] = STATE_START

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("🚆 Найти маршрут")
    markup.add(btn)

    bot.send_message(
        message.chat.id,
        "Привет! Я бот поиска маршрутов 🚆\nВыбери действие:",
        reply_markup=markup
    )


# ======================
# BUTTON HANDLER
# ======================
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    user_id = message.chat.id
    text = message.text.strip()

    state = user_state.get(user_id, STATE_START)

    # ----------------------
    # STEP 1: кнопка
    # ----------------------
    if text == "🚆 Найти маршрут":
        user_state[user_id] = STATE_WAIT_ROUTE

        bot.send_message(
            message.chat.id,
            "Введите маршрут:\nФормат: Kyiv → Lviv → 2026-06-01"
        )
        return

    # ----------------------
    # STEP 2: ввод маршрута
    # ----------------------
    if state == STATE_WAIT_ROUTE:
        user_state[user_id] = STATE_START

        try:
            parts = [p.strip() for p in text.split("→")]

            if len(parts) != 3:
                bot.send_message(
                    message.chat.id,
                    "❌ Неверный формат.\nПример: Kyiv → Lviv → 2026-06-01"
                )
                return

            from_city, to_city, date = parts

            # Заглушка (потом подключим API)
            bot.send_message(
                message.chat.id,
                f"🔎 Ищу билеты...\n\n"
                f"🚉 Откуда: {from_city}\n"
                f"🎯 Куда: {to_city}\n"
                f"📅 Дата: {date}\n\n"
                f"✅ Найдено 3 варианта (демо)"
            )

        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка: {e}")

        return

    # ----------------------
    # fallback
    # ----------------------
    bot.send_message(
        message.chat.id,
        "Нажми /start"
    )


# ======================
# START BOT
# ======================
print("BOT STARTED")

bot.infinity_polling(skip_pending=True)
