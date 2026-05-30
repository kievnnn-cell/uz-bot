import os
import re
import sqlite3
import logging
import httpx

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ---------------- CONFIG ----------------
TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_PATH = "/webhook"

UZ_URL = "https://booking.uz.gov.ua/en/purchase/search/"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bot")

app = Application.builder().token(TOKEN).build()

# ---------------- DB ----------------
db = sqlite3.connect("watch.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS watches (
    user_id INTEGER,
    from_city TEXT,
    to_city TEXT,
    train TEXT,
    wagon TEXT,
    date TEXT,
    active INTEGER DEFAULT 1
)
""")
db.commit()

# ---------------- PARSER ----------------
def parse(text: str):
    train = re.search(r"№\s*(\d+)", text)
    train = train.group(1) if train else None

    date = re.search(r"(\d{2}\.\d{2}\.\d{4})", text)
    date = date.group(1) if date else None

    wagon = "купе" if "купе" in text.lower() else "плацкарт"

    route = text.split("№")[-1].split(",")[0]
    parts = re.split(r"[–-]", route)

    if len(parts) < 2:
        return None

    return {
        "train": train,
        "from": parts[0].strip(),
        "to": parts[1].strip(),
        "wagon": wagon,
        "date": date
    }

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Отправь одну строку:\n"
        "поезд №81 Киев–Ивано-Франковск, купе, 31.05.2026"
    )

# ---------------- HANDLE USER MESSAGE ----------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    data = parse(text)

    if not data:
        await update.message.reply_text("Неверный формат")
        return

    cur.execute("""
        INSERT INTO watches VALUES (?, ?, ?, ?, ?, ?, 1)
    """, (
        user_id,
        data["from"],
        data["to"],
        data["train"],
        data["wagon"],
        data["date"]
    ))
    db.commit()

    await update.message.reply_text("Ок. Мониторинг запущен.")
