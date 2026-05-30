import os
import re
import sqlite3
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ---------------- CONFIG ----------------
TOKEN = os.getenv("BOT_TOKEN")

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

# ---------------- PARSE ----------------
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
