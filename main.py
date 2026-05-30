import os
import time
import threading
import logging
from flask import Flask, request
import telebot

# -----------------------------
# LOGGING (production-safe)
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# -----------------------------
# ENV
# -----------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

app = Flask(__name__)

# -----------------------------
# BASIC HANDLERS
# -----------------------------
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🤖 Bot is alive and running on production server."
    )


@bot.message_handler(content_types=["text"])
def echo(message):
    bot.send_message(message.chat.id, message.text)


# -----------------------------
# FLASK ROUTE (WEBHOOK)
# -----------------------------
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    try:
        json_str = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
    except Exception as e:
        logging.error(f"Webhook error: {e}")
    return "OK", 200


@app.route("/", methods=["GET", "HEAD"])
def index():
    return "Bot is running", 200


# -----------------------------
# SET WEBHOOK
# -----------------------------
def setup_webhook():
    if not BASE_URL:
        logging.warning("BASE_URL not set → webhook will NOT be configured")
        return

    webhook_url = f"{BASE_URL}{WEBHOOK_PATH}"

    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=webhook_url)
        logging.info(f"Webhook set to: {webhook_url}")
    except Exception as e:
        logging.error(f"Failed to set webhook: {e}")


# -----------------------------
# BOT THREAD (SAFE)
# -----------------------------
def run_bot():
    logging.info("BOT THREAD STARTED")
    setup_webhook()


# -----------------------------
# START APP
# -----------------------------
if __name__ == "__main__":
    logging.info("BOOT INIT")

    # start bot logic in background thread
    thread = threading.Thread(target=run_bot)
    thread.daemon = True
    thread.start()

    logging.info(f"FLASK STARTING ON PORT {PORT}")

    app.run(host="0.0.0.0", port=PORT)
