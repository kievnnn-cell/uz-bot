import os
import time
import threading
from flask import Flask
import telebot

# =====================
# CONFIG
# =====================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN is not set in environment variables")

bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

# =====================
# FLASK ROUTE (Render healthcheck)
# =====================

@app.route("/")
def home():
    return "BOT IS RUNNING 🚆", 200


# =====================
# TELEGRAM HANDLERS
# =====================

@bot.message_handler(commands=["start"])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = telebot.types.KeyboardButton("🚆 Маршруты")
    btn2 = telebot.types.KeyboardButton("ℹ️ Помощь")

    markup.add(btn1, btn2)

    bot.send_message(
        message.chat.id,
        "Привет! Я бот поиска маршрутов 🚆\nВыбери действие:",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: True)
def handle_all(message):
    text = message.text.lower()

    if "маршрут" in text:
        bot.send_message(message.chat.id, "Функция маршрутов в разработке 🚆")
    elif "помощь" in text:
        bot.send_message(message.chat.id, "Я помогу тебе найти маршрут 🚆")
    else:
        bot.send_message(message.chat.id, "Выбери кнопку меню 👇")


# =====================
# BOT START FUNCTION
# =====================

def run_bot():
    print("BOT THREAD STARTED")

    try:
        print("REMOVING WEBHOOK...")
        bot.remove_webhook()

        time.sleep(1)

        print("STARTING POLLING...")
        bot.infinity_polling(
            skip_pending=True,
            timeout=30,
            long_polling_timeout=30
        )

    except Exception as e:
        print("BOT ERROR:", e)
        time.sleep(5)
        run_bot()


# =====================
# MAIN ENTRY POINT
# =====================

if __name__ == "__main__":
    print("BOOT INIT")

    # Bot thread
    t = threading.Thread(target=run_bot)
    t.start()

    # Flask server
    print("FLASK STARTING...")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
