import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("bot")

# ---------------- ENV ----------------
TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
BASE_URL = os.getenv("BASE_URL")  # https://your-app.onrender.com

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")
if not BASE_URL:
    raise RuntimeError("BASE_URL is missing")

# ---------------- HANDLERS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot is alive!")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("pong 🟢")

# ---------------- MAIN ----------------
def main():
    logger.info("BOOT INIT")

    app = ApplicationBuilder().token(TOKEN).build()

    # handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))

    webhook_path = "/webhook"
    webhook_url = f"{BASE_URL}{webhook_path}"

    logger.info("Starting webhook mode")
    logger.info(f"Webhook URL: {webhook_url}")
    logger.info(f"Listening on port: {PORT}")

    # 🔥 ВАЖНО: production webhook server
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=webhook_url,
    )

if __name__ == "__main__":
    main()
