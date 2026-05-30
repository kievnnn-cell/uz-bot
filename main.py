import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# CONFIG
TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_PATH = "/webhook"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot is alive!")

application.add_handler(CommandHandler("start", start))


async def post_init(app: Application):
    url = f"{BASE_URL}{WEBHOOK_PATH}"
    logger.info(f"Setting webhook: {url}")
    await app.bot.set_webhook(url)


if __name__ == "__main__":
    application.post_init = post_init

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=f"{BASE_URL}{WEBHOOK_PATH}",
        drop_pending_updates=True,
    )
