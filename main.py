import os
import time
import re
import threading
import logging
from flask import Flask
import telebot

from services.uz_api import check_coupe_available

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")
PORT = int(os.getenv("PORT", 10000))

CHECK_INTERVAL = 30

logging.basicConfig(level=logging.INFO)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

subscriptions = []

# =========================
# STRICT PARSER
# =========================

def parse_query(text: str):
    pattern = r"поезд\s*№(\d+)\s+(.+?)–(.+?),\s*(купе)"
    match = re.search(pattern, text, re.IGNORECASE)

    if not match:
        return None

    return {
        "train_number": match.group(1),
        "from": match.group(2).strip(),
        "to": match.group(3).strip(),
        "class": match.group(4).lower()
    }

# =========================
# MONITOR
# =========================

def monitor():
    logging.info("MONITOR STARTED")

    while True:
        for sub in subscriptions[:]:

            try:
                if check_coupe_available(
                    sub["train_number"],
                    sub["from"],
                    sub["to"]
                ):
                    bot.send_message(
                        sub["chat_id"],
                        f"🚨 <b>БИЛЕТЫ ПОЯВИЛИСЬ!</b>\n\n"
                        f"🚆 Поезд №{sub['train_number']}\n"
                        f"📍 {sub['from']} → {sub['to']}\n"
                        f"💺 Купе доступно"
                    )
                    subscriptions.remove(sub)

            except Exception as e:
                logging.error(e)

        time.sleep(CHECK_INTERVAL)

# =========================
# TELEGRAM
# =========================

@bot.message_handler(func=lambda m: True)
def handler(m):
    parsed = parse_query(m.text)

    if not parsed:
        bot.reply_to(
            m,
            "❌ Формат строго:\n"
            "<code>поезд №81 Киев–Ивано-Франковск, купе</code>"
        )
        return

    subscriptions.append({
        "chat_id": m.chat.id,
        **parsed
    })

    bot.reply_to(
        m,
        f"✅ Принято\n\n"
        f"🚆 №{parsed['train_number']}\n"
        f"📍 {parsed['from']} → {parsed['to']}\n"
        f"💺 Купе\n\n"
        f"🔎 Мониторим..."
    )

# =========================
# FLASK
# =========================

@app.route("/")
def home():
    return "OK", 200

# =========================
# START
# =========================

def start_bot():
    logging.info("BOOT INIT")

    if BASE_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{BASE_URL}/webhook")
        logging.info(f"Webhook set: {BASE_URL}/webhook")

    bot.polling(non_stop=True)

if __name__ == "__main__":
    threading.Thread(target=start_bot).start()
    threading.Thread(target=monitor).start()

    app.run(host="0.0.0.0", port=PORT)
