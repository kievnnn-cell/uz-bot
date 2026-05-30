import os
import logging
import threading
import telebot
from flask import Flask, request

# =======================
# CONFIG
# =======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")  # https://your-app.onrender.com
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN is not set")

logging.basicConfig(level=logging.INFO)

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

app = Flask(__name__)

# =======================
# SIMPLE MEMORY (монитор)
# =======================
# user_id -> list of subscriptions
subscriptions = {}

# =======================
# BOT LOGIC
# =======================

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привет! Я монитор поездов.\n\n"
        "Формат запроса:\n"
        "поезд №81 Киев–Ивано-Франковск, купе"
    )


@bot.message_handler(func=lambda m: True)
def handle(message):
    text = message.text.lower()

    # сохраняем подписку
    user_id = message.chat.id

    if user_id not in subscriptions:
        subscriptions[user_id] = []

    subscriptions[user_id].append(text)

    bot.send_message(
        user_id,
        f"Принято:\n{text}\n\n"
        "Я буду проверять и сообщать, когда появятся места."
    )


# =======================
# MOCK MONITOR (заглушка логики)
# =======================
def monitor_loop():
    import time

    logging.info("MONITOR STARTED")

    while True:
        # тут будет API УЗ (потом подключим)
        # сейчас просто имитация

        for user_id, subs in subscriptions.items():
            for sub in subs:
                if "81" in sub:
                    # имитация события
                    bot.send_message(
                        user_id,
                        "🚆 Обновление:\n"
                        "Поезд №81 — появились места в купе!"
                    )

        time.sleep(60)


# =======================
# WEBHOOK ROUTE
# =======================
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


@app.route("/", methods=["GET"])
def index():
    return "Bot is running", 200


# =======================
# STARTUP
# =======================
def set_webhook():
    if not BASE_URL:
        logging.warning("BASE_URL is not set!")
        return

    url = BASE_URL + WEBHOOK_PATH

    try:
        bot.remove_webhook()
        logging.info("Old webhook removed")

        bot.set_webhook(url=url)
        logging.info(f"Webhook set: {url}")
    except Exception as e:
        logging.error(f"Webhook error: {e}")


if __name__ == "__main__":
    logging.info("BOOT INIT")

    set_webhook()

    # монитор в отдельном потоке
    t = threading.Thread(target=monitor_loop, daemon=True)
    t.start()

    logging.info(f"FLASK STARTING ON PORT {PORT}")
    app.run(host="0.0.0.0", port=PORT)
