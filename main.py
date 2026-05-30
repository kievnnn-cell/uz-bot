import os
import threading
from flask import Flask
import telebot

# =====================
# CONFIG
# =====================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise Exception("BOT_TOKEN is missing in environment variables")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

print("BOT STARTING...")
print("TOKEN LOADED:", bool(TOKEN))

# =====================
# FLASK SERVER
# =====================

app = Flask(__name__)

@app.route("/")
def home():
    return "OK - BOT IS RUNNING", 200


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# =====================
# BOT LOGIC
# =====================

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🚆 <b>Привет! Я бот поиска маршрутов</b>\n\nВыбери действие:"
    )


@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.send_message(
        message.chat.id,
        "ℹ️ /start - запуск\n/help - помощь"
    )


@bot.message_handler(func=lambda m: True)
def default_handler(message):
    bot.send_message(
        message.chat.id,
        f"Ты написал: {message.text}"
    )


# =====================
# START BOT (CRITICAL PART)
# =====================

def run_bot():
    try:
        # ВАЖНО: убираем webhook ВСЕГДА
        bot.remove_webhook()

        print("BOT STARTED - POLLING MODE")

        bot.infinity_polling(
            skip_pending=True,
            timeout=30,
            long_polling_timeout=30
        )

    except Exception as e:
        print("BOT ERROR:", e)


# =====================
# MAIN
# =====================

if __name__ == "__main__":
    # Flask в фоне
    threading.Thread(target=run_flask).start()

    # Bot в главном потоке
    run_bot()
