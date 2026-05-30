import os
import re
import sqlite3
import logging
import asyncio
import httpx

from datetime import datetime, timedelta
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

UZ_BASE = "https://booking.uz.gov.ua"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

app = Application.builder().token(TOKEN).build()

# ---------------- DB ----------------
conn = sqlite3.connect("watch.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS watches (
    user_id INTEGER,
    from_city TEXT,
    to_city TEXT,
    from_id TEXT,
    to_id TEXT,
    train TEXT,
    wagon TEXT,
    date TEXT,
    active INTEGER DEFAULT 1
)
""")
conn.commit()


# ---------------- PARSER ----------------
def parse(text: str):
    train = re.search(r"№\s*(\d+)", text)
    train = train.group(1) if train else None

    wagon = "купе" if "купе" in text.lower() else "плацкарт"

    date = re.search(r"(\d{2}\.\d{2}\.\d{4})", text)
    date = date.group(1) if date else None

    route = text.split("№")[-1]
    route = route.split(",")[0]
    parts = re.split(r"[–-]", route)

    if len(parts) < 2:
        return None

    return {
        "train": train,
        "from_city": parts[0].strip(),
        "to_city": parts[1].strip(),
        "wagon": wagon,
        "date": date
    }


# ---------------- STATION API ----------------
async def get_station(client, name):
    try:
        r = await client.get(f"{UZ_BASE}/en/purchase/station/{name[:3]}")
        data = r.json()
        if data.get("value"):
            return data["value"][0]["station_id"]
    except:
        return None


# ---------------- SEARCH ----------------
async def search_uz(client, state):
    r = await client.post(
        f"{UZ_BASE}/en/purchase/search/",
        data={
            "from": state["from_id"],
            "to": state["to_id"],
            "date": state["date"]
        }
    )
    return r.json()


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚆 Отправь:\n"
        "поезд №81 Киев–Ивано-Франковск, купе, 31.05.2026"
    )


# ---------------- CREATE WATCH ----------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    parsed = parse(text)

    if not parsed:
        await update.message.reply_text("❌ Неверный формат")
        return

    async with httpx.AsyncClient(timeout=20) as client:
        from_id = await get_station(client, parsed["from_city"])
        to_id = await get_station(client, parsed["to_city"])

    if not from_id or not to_id:
        await update.message.reply_text("❌ Не нашёл станции")
        return

    cur.execute("""
        INSERT INTO watches (
            user_id, from_city, to_city,
            from_id, to_id,
            train, wagon, date, active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
    """, (
        user_id,
        parsed["from_city"],
        parsed["to_city"],
        from_id,
        to_id,
        parsed["train"],
        parsed["wagon"],
        parsed["date"]
    ))
    conn.commit()

    await update.message.reply_text(
        "✅ Мониторинг запущен.\n"
        "Сообщу, когда появятся билеты."
    )


# ---------------- MONITOR JOB ----------------
async def check_jobs(context: ContextTypes.DEFAULT_TYPE):
    cur.execute("SELECT * FROM watches WHERE active=1")
    rows = cur.fetchall()

    async with httpx.AsyncClient(timeout=20) as client:
        for row in rows:
            (
                user_id,
                from_city,
                to_city,
                from_id,
                to_id,
                train,
                wagon,
                date,
                active
            ) = row

            try:
                data = await search_uz(client, {
                    "from_id": from_id,
                    "to_id": to_id,
                    "date": date
                })
            except:
                continue

            if "value" not in data:
                continue

            for t in data["value"]:
                if train and str(t.get("num")) != train:
                    continue

                for tp in t.get("types", []):
                    if wagon not in tp.get("title", "").lower():
                        continue

                    places = tp.get("places")

                    if places and places != "0":
                        await context.bot.send_message(
                            user_id,
                            f"🚨 БИЛЕТ НАЙДЕН!\n\n"
                            f"Поезд №{train}\n"
                            f"{from_city} → {to_city}\n"
                            f"{wagon}\n"
                            f"Дата: {date}\n"
                            f"Мест: {places}"
                        )

                        cur.execute(
                            "UPDATE watches SET active=0 WHERE user_id=? AND train=?",
                            (user_id, train)
                        )
                        conn.commit()


# ---------------- WEBHOOK ----------------
async def post_init(app: Application):
    url = f"{BASE_URL}{WEBHOOK_PATH}"
    await app.bot.set_webhook(url=url, drop_pending_updates=True)


app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.job_queue.run_repeating(check_jobs, interval=120, first=10)

app.post_init = post_init


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=f"{BASE_URL}{WEBHOOK_PATH}",
    )
