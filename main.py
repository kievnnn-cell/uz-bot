import os
import logging
from flask import Flask, request

import telebot

# =====================
# CONFIG
# =====================

BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN is not set")

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

app = Flask(__name__)

# =====================
# LOGGING (production-safe)
# =====================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

# =====================
# TELEGRAM WEBHOOK
# =====================

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{BASE_URL}{WEBHOOK_PATH}" if BASE_URL else None


def setup_webhook():
    try:
        if not WEBHOOK_URL:
            logger.warning("BASE_URL is not set, webhook NOT configured")
            return

        bot.remove_webhook()
        logger.info("Old webhook removed")

        bot.set_webhook(url=WEBHOOK_URL)
        logger.info(f"Webhook set to: {WEBHOOK_URL}")

    except Exception as e:
        logger.error(f"Webhook setup failed: {e}")


# =====================
# FLASK ROUTES
# =====================

@app.route("/", methods=["GET"])
def home():
    return "BOT IS RUNNING", 200


@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
        bot.process_new_updates([update])
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return "OK", 200


# =====================
# BOT LOGIC (пример)
# =====================

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Бот работает. Напиши /train")


@bot.message_handler(commands=["train"])
def train(message):
    bot.send_message(message.chat.id, "Введите маршрут (например: Киев - Львов)")


# =====================
# BOOT
# =====================

if __name__ == "__main__":
    logger.info("BOOT INIT")

    setup_webhook()

    logger.info(f"FLASK STARTING ON PORT {PORT}")
    app.run(host="0.0.0.0", port=PORT)
