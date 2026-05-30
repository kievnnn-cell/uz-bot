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
        "Отправь:\n"
        "поезд №81 Киев–Ивано-Франковск, купе, 31.05.2026"
    )


# ---------------- HANDLE ----------------
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

    await update.message.reply_text("Ок. Слежу за билетами.")


# ---------------- MONITOR ----------------
async def monitor(context: ContextTypes.DEFAULT_TYPE):
    cur.execute("SELECT * FROM watches WHERE active=1")
    rows = cur.fetchall()

    if not rows:
        return

    async with httpx.AsyncClient(timeout=20) as client:
        for r in rows:
            user_id, frm, to, train, wagon, date, active = r

            try:
                res = await client.post(
                    UZ_URL,
                    data={
                        "from": frm,
                        "to": to,
                        "date": date
                    }
                )
                data = res.json()
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
                            f"🚨 БИЛЕТ НАЙДЕН\n\n"
                            f"Поезд №{train}\n"
                            f"{frm} → {to}\n"
                            f"{wagon}\n"
                            f"{date}\n"
                            f"Мест: {places}"
                        )

                        cur.execute(
                            "UPDATE watches SET active=0 WHERE user_id=? AND train=?",
                            (user_id, train)
                        )
                        db.commit()


# ---------------- WEBHOOK ----------------
async def post_init(app: Application):
    await app.bot.set_webhook(
        url=f"{BASE_URL}{WEBHOOK_PATH}",
        drop_pending_updates=True
    )


app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.job_queue.run_repeating(monitor, interval=120, first=10)

app.post_init = post_init


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=f"{BASE_URL}{WEBHOOK_PATH}",
    )
