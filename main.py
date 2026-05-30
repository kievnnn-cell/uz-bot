print("TOKEN:", TOKEN)
print("WEBHOOK:", WEBHOOK_URL)
import os
import re
import telebot
from flask import Flask, request

TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# =========================
# 🔥 СОСТОЯНИЯ ПОЛЬЗОВАТЕЛЕЙ
# =========================
user_state = {}

STATE_IDLE = "idle"
STATE_WAIT_ROUTE = "wait_route"


print("BOT STARTED")


# =========================
# 🚀 START
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    user_state[message.chat.id] = STATE_IDLE

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🚆 Найти билеты")

    bot.send_message(
        message.chat.id,
        "Привет! Я бот поиска маршрутов 🚆\nВыбери действие:",
        reply_markup=markup
    )


# =========================
# 🎯 ОБРАБОТКА ТЕКСТА
# =========================
@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    state = user_state.get(chat_id, STATE_IDLE)

    # -------------------------
    # 1) НАЖАЛИ "НАЙТИ БИЛЕТЫ"
    # -------------------------
    if text == "🚆 Найти билеты":
        user_state[chat_id] = STATE_WAIT_ROUTE

        bot.send_message(
            chat_id,
            "Введите маршрут:\nФормат: Kyiv → Lviv → 2026-06-01"
        )
        return

    # -------------------------
    # 2) ЖДЁМ МАРШРУТ
    # -------------------------
    if state == STATE_WAIT_ROUTE:

        # парсим маршрут
        match = re.match(r"(.+?)→(.+?)→(\d{4}-\d{2}-\d{2})", text)

        if not match:
            bot.send_message(
                chat_id,
                "❌ Неверный формат!\n\nПример:\nKyiv → Lviv → 2026-06-01"
            )
            return

        origin = match.group(1).strip()
        destination = match.group(2).strip()
        date = match.group(3).strip()

        # сохраняем данные
        user_state[chat_id] = {
            "state": "route_ready",
            "origin": origin,
            "destination": destination,
            "date": date
        }

        # кнопки следующего шага
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("🔎 Найти билеты", callback_data="search"),
            telebot.types.InlineKeyboardButton("✏️ Изменить", callback_data="edit")
        )

        bot.send_message(
            chat_id,
            f"🚆 Маршрут принят:\n📍 {origin} → {destination}\n📅 {date}",
            reply_markup=markup
        )
        return

    # -------------------------
    # 3) если просто текст
    # -------------------------
    bot.send_message(chat_id, "Нажми кнопку 🚆 Найти билеты")


# =========================
# 🔘 INLINE КНОПКИ
# =========================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    data = call.data

    user_data = user_state.get(chat_id, {})

    # -------------------------
    # 🔎 ПОИСК
    # -------------------------
    if data == "search":
        if isinstance(user_data, dict) and user_data.get("state") == "route_ready":

            bot.send_message(
                chat_id,
                f"🔎 Ищу билеты...\n\n"
                f"{user_data['origin']} → {user_data['destination']}\n"
                f"Дата: {user_data['date']}"
            )

        else:
            bot.send_message(chat_id, "Сначала введи маршрут")

    # -------------------------
    # ✏️ ИЗМЕНИТЬ
    # -------------------------
    elif data == "edit":
        user_state[chat_id] = STATE_WAIT_ROUTE

        bot.send_message(
            chat_id,
            "Введите новый маршрут:\nФормат: Kyiv → Lviv → 2026-06-01"
        )


# =========================
# 🌐 WEBHOOK
# =========================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


@app.route("/")
def index():
    return "Bot is alive", 200


# =========================
# 🚀 START SERVER
# =========================
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))

    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

    print("WEBHOOK SET:", WEBHOOK_URL)

    app.run(host="0.0.0.0", port=PORT)
