import os
import logging
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

# ---------------- BOT ----------------
application = Application.builder().token(TOKEN).build()

# ---------------- HANDLERS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot is alive!")

application.add_handler(CommandHandler("start", start))


# ---------------- WEBHOOK STARTUP ----------------
async def post_init(app: Application):
    """Runs after bot init"""
    url = f"{BASE_URL}{WEBHOOK_PATH}"
    logger.info(f"Setting webhook: {url}")
    await app.bot.set_webhook(url=url)


# ---------------- ENTRY ----------------
if __name__ == "__main__":
    logger.info("BOOT INIT")

    application.post_init = post_init

    logger.info("Starting webhook server...")

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=f"{BASE_URL}{WEBHOOK_PATH}",
        drop_pending_updates=True,
    )
