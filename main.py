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

# -------------------
# FLASK
# -------------------
@app.route("/")
def home():
    return "BOT RUNNING 🚆", 200


# -------------------
# HANDLERS
# -------------------
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привет! Я бот маршрутов 🚆\nНапиши /help"
    )


@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.send_message(message.chat.id, "Я помогу найти маршрут 🚆")


# -------------------
# BOT LOOP (FIXED)
# -------------------
def run_bot():
    print("BOT THREAD STARTED")

    try:
        print("REMOVING WEBHOOK...")

        bot.remove_webhook()
        time.sleep(2)

        print("WEBHOOK REMOVED")
        print("STARTING POLLING 🚆")

        # ВАЖНО: try/except ВНУТРИ polling
        while True:
            try:
                bot.infinity_polling(
                    skip_pending=True,
                    timeout=20,
                    long_polling_timeout=20
                )
            except Exception as e:
                print("POLLING ERROR:", e)
                time.sleep(5)

    except Exception as e:
        print("FATAL BOT ERROR:", e)
        time.sleep(5)
        run_bot()


# -------------------
# MAIN
# -------------------
if __name__ == "__main__":
    print("BOOT INIT")

    t = threading.Thread(target=run_bot)
    t.daemon = True
    t.start()

    print("FLASK STARTING...")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
