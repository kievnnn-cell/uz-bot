import os
import time
import logging
import threading
from flask import Flask, request

import telebot

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN is not set")

if not BASE_URL:
    print("WARNING: BASE_URL is not set, webhook may fail")

WEBHOOK_URL = f"{BASE_URL}{WEBHOOK_PATH}"

# =========================
# LOGGING
# =========================

logging.basicConfig(level=logging.INFO)

# =========================
# BOT INIT
# =========================

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# =========================
# FLASK APP
# =========================

app = Flask(__name__)

# =========================
# SIMPLE STATE (for MVP)
# =========================
subscriptions = {}

# =========================
# TELEGRAM HANDLERS
# =========================

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🚆 Бот запущен.\n\n"
        "Формат запроса:\n"
        "поезд №81 Киев–Ивано-Франковск, купе"
    )

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    text = message.text.lower()

    # простейший парсер (MVP)
    if "поезд" in text:
        chat_id = message.chat.id

        subscriptions[chat_id] = text

        bot.send_message(
            chat_id,
            f"✅ Принято в мониторинг:\n\n{text}\n\n"
            "Я буду проверять наличие купе и уведомлять."
        )
    else:
        bot.send_message(
            message.chat.id,
            "Напиши запрос в формате:\n"
            "поезд №81 Киев–Ивано-Франковск, купе"
        )

# =========================
# WEBHOOK ENDPOINT
# =========================

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# =========================
# MONITOR (placeholder)
# =========================

def monitor_loop():
    """
    Здесь позже подключим uz_api.py
    Сейчас просто держит процесс живым
    """
    while True:
        try:
            # TODO: проверка УЗ билетов
            time.sleep(30)
        except Exception as e:
            logging.error(f"Monitor error: {e}")
            time.sleep(10)

# =========================
# STARTUP
# =========================

def start_bot():
    logging.info("BOOT INIT")

    # ⚠️ ВАЖНО: убираем старый webhook
    try:
        bot.remove_webhook()
        logging.info("Old webhook removed")
    except Exception as e:
        logging.warning(f"Webhook remove failed: {e}")

    # ставим новый webhook
    bot.set_webhook(url=WEBHOOK_URL)
    logging.info(f"Webhook set: {WEBHOOK_URL}")

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    # старт Telegram bot thread (NO polling!)
    threading.Thread(target=start_bot).start()

    # старт монитора
    threading.Thread(target=monitor_loop, daemon=True).start()
    logging.info("MONITOR STARTED")

    # старт Flask
    logging.info(f"FLASK STARTING ON PORT {PORT}")
    app.run(host="0.0.0.0", port=PORT)
