import os
import logging
import re

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------------- CONFIG ----------------
TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_PATH = "/webhook"

if not TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

if not BASE_URL:
    raise RuntimeError("BASE_URL missing")

# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("bot")

# ---------------- BOT ----------------
app = Application.builder().token(TOKEN).build()


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Отправь запрос, например:\n"
        "поезд №81 Киев–Ивано-Франковск, купе"
    )


# ---------------- PARSER ----------------
def parse_query(text: str):
    """
    Очень простой парсер под твою задачу
    """

    number = None
    route = None
    wagon = None

    # номер поезда
    m = re.search(r"№\s*(\d+)", text)
    if m:
        number = m.group(1)

    # вагон
    if "купе" in text.lower():
        wagon = "Купе"
    elif "плацкарт" in text.lower():
        wagon = "Плацкарт"

    # маршрут (очень грубо)
    if "–" in text or "-" in text:
        route = text.split("№")[-1]
        route = re.sub(r"[,\.\n]", "", route).strip()

    return number, route, wagon


# ---------------- MAIN TEXT HANDLER ----------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    logger.info(f"INPUT: {text}")

    number, route, wagon = parse_query(text)

    response = "🚆 Результат поиска:\n"

    if number:
        response += f"• Поезд №{number}\n"
    if route:
        response += f"• Маршрут: {route}\n"
    if wagon:
        response += f"• Тип вагона: {wagon}\n"

    if not any([number, route, wagon]):
        response = "❌ Не понял запрос. Пример:\nпоезд №81 Киев–Ивано-Франковск, купе"

    await update.message.reply_text(response)


# ---------------- HANDLERS ----------------
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))


# ---------------- WEBHOOK SETUP ----------------
async def post_init(application: Application):
    url = f"{BASE_URL}{WEBHOOK_PATH}"

    logger.info(f"Setting webhook: {url}")

    await application.bot.delete_webhook(drop_pending_updates=True)
    await application.bot.set_webhook(url=url)

    info = await application.bot.get_webhook_info()
    logger.info(f"Webhook info: {info}")


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.post_init = post_init

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=f"{BASE_URL}{WEBHOOK_PATH}",
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )
