import os
import logging
from flask import Flask

from bot import bot
from routes import webhook_blueprint

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# register webhook route
app.register_blueprint(webhook_blueprint)

def setup_webhook():
    token = os.getenv("BOT_TOKEN")
    base_url = os.getenv("BASE_URL")
    path = os.getenv("WEBHOOK_PATH", "/webhook")

    if not token or not base_url:
        logging.warning("Missing BOT_TOKEN or BASE_URL")
        return

    url = base_url + path

    try:
        bot.remove_webhook()
        logging.info("Old webhook removed")

        bot.set_webhook(url=url)
        logging.info(f"Webhook set: {url}")

    except Exception as e:
        logging.error(f"Webhook error: {e}")

def start():
    logging.info("BOOT INIT")
    setup_webhook()
    logging.info("MONITOR STARTED")

if __name__ == "__main__":
    start()

    port = int(os.getenv("PORT", 10000))
    logging.info(f"FLASK STARTING ON PORT {port}")

    app.run(host="0.0.0.0", port=port)
