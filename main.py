import os
import time
import threading
import telebot
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN is missing")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ---------------- FLASK ----------------
@app.route("/")
def home():
    return "BOT RUNNING 🚆", 200


# ---------------- HANDLERS ----------------
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привет! Я бот маршрутов 🚆"
    )


# ---------------- BOT ----------------
def run_bot():
    print("BOT THREAD STARTED")
    print("STARTING POLLING 🚆")

    while True:
        try:
            bot.infinity_polling(
                skip_pending=True,
                timeout=10,
                long_polling_timeout=10
            )

        except Exception as e:
            print("POLLING ERROR:", e)
            time.sleep(3)


# ---------------- MAIN ----------------
if __name__ == "__main__":
    print("BOOT INIT")

    t = threading.Thread(target=run_bot)
    t.daemon = True
    t.start()

    print("FLASK STARTING...")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
