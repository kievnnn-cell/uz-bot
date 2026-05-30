import os
import logging
import re
import httpx

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ---------------- CONFIG ----------------
TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_PATH = "/webhook"

UZ_API = "https://booking.uz.gov.ua/en"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

app = Application.builder().token(TOKEN).build()


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚆 Введи:\n"
        "поезд №81 Киев–Ивано-Франковск, купе, 31.05.2026"
    )


# ---------------- PARSER (STRICT) ----------------
def parse(text: str):
    """
    Формат:
    поезд №81 Киев–Ивано-Франковск, купе, 31.05.2026
    """

    train_number = None
    wagon = None
    date = None
    from_city = None
    to_city = None

    # номер поезда
    m = re.search(r"№\s*(\d+)", text)
    if m:
        train_number = m.group(1)

    # дата
    d = re.search(r"(\d{2}\.\d{2}\.\d{4})", text)
    if d:
        date = d.group(1)

    # вагон
    if "купе" in text.lower():
        wagon = "купе"
    elif "плацкарт" in text.lower():
        wagon = "плацкарт"

    # маршрут
    route_match = re.search(r"№\s*\d+\s*(.+)", text)
    if route_match:
        route = route_match.group(1)
        route = route.split(",")[0]
        parts = re.split(r"[–-]", route)

        if len(parts) >= 2:
            from_city = parts[0].strip()
            to_city = parts[1].strip()

    return train_number, from_city, to_city, wagon, date


# ---------------- UZ SEARCH ----------------
async def search_uz(from_city, to_city, date):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            "https://booking.uz.gov.ua/en/purchase/search/",
            data={
                "from": from_city,
                "to": to_city,
                "date": date
            }
        )
        return r.json()


# ---------------- HANDLER ----------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    logger.info(f"INPUT: {text}")

    train_number, from_city, to_city, wagon, date = parse(text)

    if not all([from_city, to_city, date]):
        await update.message.reply_text("❌ Неправильный формат запроса")
        return

    try:
        data = await search_uz(from_city, to_city, date)
    except Exception as e:
        logger.error(str(e))
        await update.message.reply_text("❌ Ошибка УЗ API")
        return

    if "value" not in data:
        await update.message.reply_text("❌ Нет данных")
        return

    # ---------------- FILTER ----------------
    result_msg = "🚆 Найдено:\n\n"
    found = False

    for train in data["value"]:
        num = str(train.get("num"))

        # фильтр по номеру поезда (ВАЖНО)
        if train_number and num != train_number:
            continue

        found = True
        result_msg += f"🚆 Поезд №{num}\n"
        result_msg += f"{train.get('from')} → {train.get('to')}\n"

        if "types" in train:
            for t in train["types"]:
                title = t.get("title", "").lower()

                # фильтр по вагону
                if wagon and wagon not in title:
                    continue

                result_msg += f"  • {t.get('title')}: {t.get('places')}\n"

        result_msg += "\n"

    if not found:
        result_msg = "❌ По этому запросу ничего не найдено"

    await update.message.reply_text(result_msg)


# ---------------- WEBHOOK ----------------
async def post_init(app: Application):
    url = f"{BASE_URL}{WEBHOOK_PATH}"
    await app.bot.set_webhook(url=url, drop_pending_updates=True)


app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.post_init = post_init


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=f"{BASE_URL}{WEBHOOK_PATH}",
    )
