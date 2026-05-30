import os
from flask import Flask, request
import telebot

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise Exception("BOT_TOKEN missing")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Render URL
BASE_URL = os.environ.get("RENDER_EXTERNAL_URL")

if not BASE_URL:
    raise Exception("RENDER_EXTERNAL_URL missing")

# webhook endpoint БЕЗ токена в URL
WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = BASE_URL + WEBHOOK_PATH

# reset webhook
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

print("BOT STARTED")
print("WEBHOOK ACTIVE")

# ================= HANDLERS =================

@bot.message_handler(commands=['start'])
def start(message):
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🚆 Маршруты", "ℹ️ Помощь")

    bot.send_message(
        message.chat.id,
        "Привет! Я бот поиска маршрутов 🚆\nВыбери действие:",
        reply_markup=kb
    )


@bot.message_handler(func=lambda m: True)
def handler(message):
    if message.text == "🚆 Маршруты":
        bot.send_message(message.chat.id, "Введите маршрут: Киев → Львов")

    elif message.text == "ℹ️ Помощь":
        bot.send_message(message.chat.id, "Просто выбери маршрут и отправь направление")

    else:
        bot.send_message(message.chat.id, "Нажми /start")


# ================= WEBHOOK =================

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode("utf-8"))
    bot
