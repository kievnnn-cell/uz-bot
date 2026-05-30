import os
import telebot
from flask import Flask, request

# =====================
# ENV VARIABLES (Render)
# =====================
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    raise ValueError("TOKEN is missing in environment variables")

if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL is missing in environment variables")

# =====================
# BOT + APP
# =====================
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

print("BOT STARTED")


# =====================
# START COMMAND
# =====================
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🚆 Найти билет")

    bot.send_message(
        message.chat.id,
        "Привет! Я бот поиска маршрутов 🚆\nВыбери действие:",
        reply_markup=markup
    )


# =====================
# TEXT HANDLER (простая логика)
# =====================
user_state = {}

@bot.message_handler(func=lambda m: True)
def handle(message):
    chat_id = message.chat.id
    text = message.text

    # шаг 1
    if text == "🚆 Найти билет":
        user_state[chat_id] = "await_route"
        bot.send_message(chat_id, "Введите маршрут:\nФормат: Kyiv → Lviv → 2026-06-01")
        return

    # шаг 2
    if user_state.get(chat_id) == "await_route":
        try:
            parts = [p.strip() for p in text.split("→")]

            if len(parts) != 3:
                bot.send_message(chat_id, "❌ Ошибка формата. Используй: Kyiv → Lviv → 2026-06-01")
                return

            from_city, to_city, date = parts

            user_state[chat_id] = "done"

            bot.send_message(
                chat_id,
                f"🚆 Маршрут принят:\n📍 Откуда: {from_city}\n📍 Куда: {to_city}\n📅 Дата: {date}\n\n"
                f"🔎 Ищу билеты..."
            )

            # сюда позже подключим API / расписание / tickets

        except Exception as e:
            bot.send_message(chat_id, f"Ошибка: {str(e)}")


# =====================
# WEBHOOK ENDPOINT
# =====================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


# =====================
# HEALTH CHECK
# =====================
@app.route("/")
def index():
    return "Bot is alive", 200


# =====================
# STARTUP
# =====================
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))

    print("WEBHOOK URL:", WEBHOOK_URL)

    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

    print("WEBHOOK SET")

    app.run(host="0.0.0.0", port=PORT)
