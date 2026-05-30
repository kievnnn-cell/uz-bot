import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ---------------- CONFIG ----------------
TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")  # https://your-app.onrender.com
WEBHOOK_PATH = "/webhook"
PORT = int(os.getenv("PORT", 10000))

# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("bot")

# ---------------- FLASK ----------------
app = Flask(__name__)

# ---------------- BOT ----------------
application = Application.builder().token(TOKEN).build()


# ---------------- HANDLERS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot is alive!")


application.add_handler(CommandHandler("start", start))


# ---------------- WEBHOOK ROUTE ----------------
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    """Telegram sends updates here"""
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)

    # IMPORTANT: correct async-safe execution
    asyncio.run(application.process_update(update))

    return "OK"


@app.route("/", methods=["GET"])
def index():
    return "Bot is running"


# ---------------- SET WEBHOOK ----------------
async def set_webhook():
    url = f"{BASE_URL}{WEBHOOK_PATH}"
    logger.info(f"Setting webhook: {url}")
    await application.bot.set_webhook(url=url)


# ---------------- START APP ----------------
async def run():
    logger.info("BOOT INIT")

    await application.initialize()
    await set_webhook()

    logger.info("Bot ready (webhook mode)")

# ---------------- ENTRY ----------------
if __name__ == "__main__":
    asyncio.run(run())

    logger.info("Flask starting...")
    app.run(host="0.0.0.0", port=PORT)
