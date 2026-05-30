import os
import logging
import time
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # optional
PORT = int(os.getenv("PORT", "8080"))
USE_WEBHOOK = os.getenv("USE_WEBHOOK", "false").lower() == "true"

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in environment variables")

# ======================
# LOGGING (ROBUST)
# ======================
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("bot")

# ======================
# HANDLERS
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("🤖 Бот запущен и работает стабильно.")
    except Exception as e:
        logger.error(f"/start error: {e}")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("ℹ️ Просто отправь сообщение — я его повторю.")
    except Exception as e:
        logger.error(f"/help error: {e}")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message and update.message.text:
            await update.message.reply_text(update.message.text)
    except Exception as e:
        logger.error(f"echo error: {e}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling update:", exc_info=context.error)
    # не падаем никогда


# ======================
# MAIN STARTUP
# ======================
def main():
    while True:
        try:
            logger.info("Starting bot...")

            app = Application.builder().token(TOKEN).build()

            # handlers
            app.add_handler(CommandHandler("start", start))
            app.add_handler(CommandHandler("help", help_cmd))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

            app.add_error_handler(error_handler)

            # ======================
            # WEBHOOK MODE
            # ======================
            if USE_WEBHOOK and WEBHOOK_URL:
                logger.info("Running in WEBHOOK mode")

                app.run_webhook(
                    listen="0.0.0.0",
                    port=PORT,
                    url_path=TOKEN,
                    webhook_url=f"{WEBHOOK_URL}/{TOKEN}",
                )

            # ======================
            # POLLING MODE
            # ======================
            else:
                logger.info("Running in POLLING mode")

                app.run_polling(
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=True,
                )

        except Exception as e:
            logger.critical(f"BOT CRASHED: {e}")

            # авто-рестарт через 5 секунд
            time.sleep(5)
            logger.info("Restarting bot...")


if __name__ == "__main__":
    main()
