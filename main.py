import os
from flask import Flask, request
import telebot

# =========================
# CONFIG
# =========================

TOKEN = os.environ.get("BOT_TOKEN")  # токен только из Render env
if not TOKEN:
    raise Exception("BOT_TOKEN is not set in environment variables")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

BASE_URL = os.environ.get("RENDER_EXTERNAL_URL")

if not BASE_URL:
    raise Exception("RENDER_EXTERNAL_URL is not set (Render provides it automatically)")

WEBHOOK_URL = f"{BASE_URL}/{TOKEN}"

# =========================
# STARTUP CLEAN WEBHOOK
# =========================

bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

print("BOT STARTED")
print("WEBHOOK:", WEBHOOK_URL)

# =========================
# HANDLERS (V4 UI START)
# =========================

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🚆 Поиск маршрута", "ℹ️ Помощь")

    bot.send_message(
        message.chat.id,
        "Привет! Я бот поиска маршрутов 🚆\nВыбери действие:",
        reply_markup=markup
    )


@bot.message_handler(func=lambda m: True)
def router(message):
    text = message.text

    if text == "🚆 Поиск маршрута":
        bot.send_message(message.chat.id, "Введи маршрут:\nНапример: Киев → Львов")

    elif text == "ℹ️ Помощь":
        bot.send_message(message.chat.id, "Я помогу найти маршрут поездов 🚆")

    else:
        bot.send_message(message.chat.id, f"Принял запрос: {text}")

# =========================
# WEBHOOK ENDPOINT
# =========================

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


@app.route("/", methods=["GET"])
def index():
    return "BOT IS RUNNING", 200


# =========================
# RUN
# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
