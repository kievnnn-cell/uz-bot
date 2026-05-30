import os
import telebot
from flask import Flask, request

print("BOT STARTING...")

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise Exception("BOT_TOKEN missing in environment variables")

bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# 🔥 КРИТИЧЕСКИ ВАЖНО: сброс старого webhook
bot.remove_webhook()

# Устанавливаем новый webhook
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-app.onrender.com")
bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

print("WEBHOOK SET:", WEBHOOK_URL)


# --- START HANDLER ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я бот поиска маршрутов 🚆\nВыбери действие:")


# --- WEBHOOK ENDPOINT ---
@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


# --- HEALTH CHECK ---
@app.route('/', methods=['GET'])
def index():
    return "BOT IS RUNNING", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
