import os
import threading
from flask import Flask, request
import telebot

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN")  # только из environment
if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in environment variables")

BASE_URL = os.getenv("BASE_URL")  # например https://your-app.onrender.com

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

# =========================
# BOT LOGIC
# =========================

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Бот запущен и работает нормально."
    )

@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.send_message(message.chat.id, f"Ты написал: {message.text}")


# =========================
# FLASK ROUTES (WEBHOOK)
# =========================

@app.route("/", methods=["GET"])
def home():
    return "Bot is alive", 200


@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


# =========================
# BOT STARTUP
# =========================

def set_webhook():
    if not BASE_URL:
        print("WARNING: BASE_URL is not set, webhook will not be configured")
        return

    webhook_url = f"{BASE_URL}/{TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    print("Webhook set:", webhook_url)


def run_bot():
    set_webhook()
    print("BOT THREAD STARTED")


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))

    # бот в отдельном потоке
    threading.Thread(target=run_bot).start()

    # flask сервер (Render требует PORT)
   
