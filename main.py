import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ----------------- CONFIG -----------------
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = "/webhook"
BASE_URL = os.getenv("BASE_URL")  # https://your-app.onrender.com

# ----------------- LOGGING -----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("bot")

# ----------------- FLASK -----------------
app = Flask(__name__)

# ----------------- BOT -----------------
application = Application.builder().token(TOKEN).build()


# ----------------- HANDLERS -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot is alive!")


application.add_handler(CommandHandler("start", start))


# ----------------- WEBHOOK ROUTE -----------------
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.create_task(application.process_update(update))
    return "OK"


@app.route("/", methods=["GET"])
def index():
    return "Bot is running"


# ----------------- INIT WEBHOOK -----------------
def set_webhook():
    url = f"{BASE_URL}{WEBHOOK_PATH}"
    logger.info(f"Setting webhook: {url}")
    application.bot.set_webhook(url=url)


# ----------------- START -----------------
def main():
    logger.info("BOOT INIT")

    # IMPORTANT: initialize application properly (fix asyncio issue)
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    application.initialize()
    set_webhook()

    logger.info("Flask starting...")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))


if __name__ == "__main__":
    main()
