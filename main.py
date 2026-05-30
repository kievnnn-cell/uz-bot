import os
import threading
from flask import Flask
import telebot

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# =========================
# FLASK (for Render healthcheck)
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return "BOT IS RUNNING", 200


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# =========================
# BOT HANDLERS
# =========================

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
        "ℹ️ Доступные команды:\n/start - запуск\n/help - помощь"
    )

# пример кнопочного меню (V4 база UI)
@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.send_message(
        message.chat.id,
        f"Ты написал: <b>{message.text}</b>"
    )


# =========================
# STARTUP
# =========================

def run_bot():
    print("BOT STARTING...")
    print("TOKEN LOADED:", bool(TOKEN))

    # ВАЖНО: убираем webhook полностью (иначе 409 ошибка снова)
    bot.remove_webhook()

    print("BOT STARTED - polling now")
    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    # Flask в отдельном потоке
    threading.Thread(target=run_flask).start()

    # Bot в главном потоке
    run_bot()
