import os
import telebot
from flask import Flask
import threading

print("BOOT INIT")

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise Exception("BOT_TOKEN missing")

bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

@app.route("/")
def home():
    return "OK", 200


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


def run_bot():
    print("BOT THREAD STARTED")

    try:
        bot.remove_webhook()
        print("WEBHOOK CLEARED")

        bot.infinity_polling(
            skip_pending=True,
            timeout=20,
            long_polling_timeout=20
        )

    except Exception as e:
        print("BOT ERROR:", repr(e))


if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    run_bot()
