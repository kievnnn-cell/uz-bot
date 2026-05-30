import os
import logging
import httpx
import re

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
    await update.message.reply_text("🚆 Отправь: поезд №81 Киев–Ивано-Франковск, купе")


# ---------------- UZ API HELPERS ----------------

async def find_station(client, name: str):
    """Поиск станции в УЗ API"""
    r = await client.post(
        f"{UZ_API}/purchase/station/{name[:3]}",
        data={}
    )
    data = r.json()
    if "value" in data and data["value"]:
        return data["value"][0]["station_id"], data["value"][0]["title"]
    return None, None


async def search_trains(from_id, to_id):
    """Поиск поездов"""
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://booking.uz.gov.ua/en/purchase/search/",
            data={
                "from": from_id,
                "to": to_id,
                "date": "30.05.2026"
            }
        )
        return r.json()


# ---------------- PARSE INPUT ----------------

def parse(text):
    number = re.search(r"№\s*(\d+)", text)
    train_number = number.group(1) if number else None

    route = text.split("№")[-1] if "№" in text else text

    parts = re.split(r"[-–]", route)
    if len(parts) >= 2:
        return train_number, parts[0].strip(), parts[1].split(",")[0].strip()

    return train_number, None, None


# ---------------- MAIN HANDLER ----------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    logger.info(f"INPUT: {text}")

    train_number, from_city, to_city = parse(text)

    async with httpx.AsyncClient() as client:
        from_id, from_name = await find_station(client, from_city)
        to_id, to_name = await find_station(client, to_city)

        if not from_id or not to_id:
            await update.message.reply_text("❌ Не нашёл станции")
            return

        result = await client.post(
            "https://booking.uz.gov.ua/en/purchase/search/",
            data={
                "from": from_id,
                "to": to_id,
                "date": "30.05.2026"
            }
        )

        data = result.json()

    # ---------------- RESPONSE ----------------
    if "value" not in data:
        await update.message.reply_text("❌ Нет данных УЗ")
        return

    msg = "🚆 Результаты УЗ:\n\n"

    for train in data["value"][:5]:
        msg += f"Поезд {train.get('num')} | {train.get('from')} → {train.get('to')}\n"

        if "types" in train:
            for t in train["types"]:
                msg += f"  - {t.get('title')}: {t.get('places', 'нет мест')}\n"

        msg += "\n"

    await update.message.reply_text(msg)


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
