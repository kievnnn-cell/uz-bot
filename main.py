import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ---------------- CONFIG ----------------
TOKEN = os.getenv("BOT_TOKEN")  # НЕ ХРАНИ В КОДЕ
BASE_URL = os.getenv("BASE_URL")  # https://your-app.onrender.com
PORT = int(os.getenv("PORT", 10000))

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{BASE_URL}{WEBHOOK_PATH}"

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


# ---------------- MAIN ----------------
def main():
    logger.info("BOOT INIT")

    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")
    if not BASE_URL:
        raise RuntimeError("BASE_URL is not set")

    logger.info(f"Webhook URL: {WEBHOOK_URL}")

    # ❗ ВАЖНО: НЕ создаём event loop вручную
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=WEBHOOK_URL,
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
