import os
import telebot
from telebot import types
from flask import Flask, request

TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# память состояний (простая версия)
user_state = {}

# ---------------- START ----------------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_state[user_id] = "waiting_route"

    markup = types.ReplyKeyboardRemove()

    bot.send_message(
        user_id,
        "🚆 Привет! Я бот поиска маршрутов\n\n"
        "Введите маршрут в формате:\n"
        "Kyiv → Lviv → 2026-06-01",
        reply_markup=markup
    )

# ---------------- TEXT HANDLER ----------------
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.chat.id
    text = message.text

    state = user_state.get(user_id)

    # STEP 1: ждём маршрут
    if state == "waiting_route":

        try:
            parts = [p.strip() for p in text.split("→")]

            if len(parts) != 3:
                bot.send_message(user_id, "❌ Неверный формат. Пример:\nKyiv → Lviv → 2026-06-01")
                return

            from_city, to_city, date = parts

            user_state[user_id] = {
                "step": "ready",
                "from": from_city,
                "to": to_city,
                "date": date
            }

            # inline кнопки
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔍 Найти билеты", callback_data="search"))
            markup.add(types.InlineKeyboardButton("📅 Расписание", callback_data="schedule"))
            markup.add(types.InlineKeyboardButton("🔄 Новый маршрут", callback_data="reset"))

            bot.send_message(
                user_id,
                f"🚆 Маршрут принят:\n"
                f"📍 {from_city} → {to_city}\n"
                f"📅 {date}\n\n"
                f"Выберите действие:",
                reply_markup=markup
            )

        except Exception as e:
            bot.send_message(user_id, f"Ошибка: {e}")

# ---------------- BUTTONS ----------------
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.message.chat.id
    data = call.data

    state = user_state.get(user_id, {})

    if data == "search":
        bot.send_message(
            user_id,
            f"🔎 Ищу билеты:\n{state.get('from')} → {state.get('to')} ({state.get('date')})\n\n"
            "⚙️ (здесь позже подключим API)"
        )

    elif data == "schedule":
        bot.send_message(
            user_id,
            "📅 Показываю расписание...\n(пока заглушка, добавим API позже)"
        )

    elif data == "reset":
        user_state[user_id] = "waiting_route"
        bot.send_message(user_id, "Введите новый маршрут:\nKyiv → Lviv → 2026-06-01")

    bot.answer_callback_query(call.id)

# ---------------- WEBHOOK ----------------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# ---------------- HEALTH ----------------
@app.route("/")
def index():
    return "Bot is alive", 200

# ---------------- START APP ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

    print("BOT STARTED")
    print("WEBHOOK SET:", WEBHOOK_URL)

    app.run(host="0.0.0.0", port=port)
