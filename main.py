import os
import logging
import traceback

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    Defaults,
)

# ---------------- CONFIG ----------------
TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")  # https://your-app.onrender.com
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_PATH = "/webhook"

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

if not BASE_URL:
    raise RuntimeError("BASE_URL is missing")

# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("bot")

# ---------------- BOT APP ----------------
application = Application.builder().token(TOKEN).build()


# ---------------- SAFE HANDLER WRAPPER ----------------
async def safe_handler(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            return await func(update, context)
        except Exception as e:
            logger.error("Handler error: %s", str(e))
            logger.error(traceback.format_exc())

            if update.effective_message:
                await update.effective_message.reply_text(
                    "⚠️ Error occurred, but bot is still running."
                )

    return wrapper


# ---------------- COMMANDS ----------------
@safe_handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Production bot is alive!")


@safe_handler
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 pong")


application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("ping", ping))


# ---------------- WEBHOOK AUTO SETUP ----------------
async def post_init(app: Application):
    url = f"{BASE_URL}{WEBHOOK_PATH}"

    logger.info("Setting webhook → %s", url)

    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.bot.set_webhook(url=url)

    info = await app.bot.get_webhook_info()
    logger.info("Webhook info: %s", info)


# ---------------- HEALTH CHECK ----------------
async def health_check():
    logger.info("Health check passed")


# ---------------- RUN ----------------
if __name__ == "__main__":
    logger.info("BOOT INIT")

    application.post_init = post_init

    # IMPORTANT: full production webhook server
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=f"{BASE_URL}{WEBHOOK_PATH}",
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )
