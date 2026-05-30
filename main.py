import os
import time
import threading
import telebot
from flask import Flask

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN is not set in environment variables")

bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

# =========================
# FLASK (Render healthcheck)
# =========================

@app.route("/")
def home():
    return "BOT IS RUNNING 🚆", 200


# =========================
# TELEGRAM BOT HANDLERS
# =========================

@bot.message_handler(commands=["start"])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add(
        telebot.types.KeyboardButton("🚆 Маршруты"),
        telebot.types.KeyboardButton("ℹ️ Помощь")
    )

    bot.send_message(
        message.chat.id,
        "Привет! Я бот поиска маршрутов 🚆\nВыбери действие:",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: True)
def handler(message):
    text = message.text.lower()

    if "маршрут" in text:
        bot.send_message(message.chat.id, "Функция маршрутов в разработке 🚆")
    elif "помощь" in text:
        bot.send_message(message.chat.id, "Я помогу тебе найти маршрут 🚆")
    else:
        bot.send_message(message.chat.id, "Используй кнопки меню 👇")


# =========================
# BOT RUN LOOP
# =========================

def run_bot():
    print("BOT THREAD STARTED")

    try:
        print("REMOVING WEBHOOK...")
        bot.remove_webhook()

        time.sleep(1)

        print("STARTING POLLING 🚆")

        bot.infinity_polling(
            skip_pending=True,
            timeout=30,
            long_polling_timeout=30
        )

    except Exception as e:
        print("BOT ERROR:", str(e))
        time.sleep(5)
        run_bot()


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    print("BOOT INIT")

    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Start Flask
    print("FLASK STARTING...")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
