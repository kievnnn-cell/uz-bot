import os
import re
import telebot
from flask import Flask, request, abort

# --- ENV ---
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    raise Exception("TOKEN is not set")

if not WEBHOOK_URL:
    raise Exception("WEBHOOK_URL is not set")

# --- BOT ---
bot = telebot.TeleBot(TOKEN, threaded=False)

# --- APP ---
app = Flask(__name__)

print("BOT STARTED")
print("WEBHOOK:", WEBHOOK_URL)

# -----------------------------
# /start
# -----------------------------
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🤖 Бот запущен!\n\n"
        "Отправь маршрут в формате:\n"
        "Kyiv → Lviv → 2026-06-01"
    )

# -----------------------------
# TEXT HANDLER (ГЛАВНЫЙ)
# -----------------------------
@bot.message_handler(content_types=['text'])
def handle_text(message):
    text = message.text.strip()

    print("IN:", text)

    # --- пробуем вытащить маршрут ---
    match = re.search(r"(.+?)\s*→\s*(.+?)\s*→\s*(\d{4}-\d{2}-\d{2})", text)

    if match:
        from_city = match.group(1).strip()
        to_city = match.group(2).strip()
        date = match.group(3).strip()

        bot.send_message(
            message.chat.id,
            f"🚆 Маршрут принят:\n"
            f"📍 Откуда: {from_city}\n"
            f"📍 Куда: {to_city}\n"
            f"📅 Дата: {date}"
        )
        return

    # --- если просто дата ---
    if re.match(r"\d{4}-\d{2}-\d{2}", text):
        bot.send_message(message.chat.id, f"📅 Дата получена: {text}")
        return

    # --- если просто текст ---
    bot.send_message(
        message.chat.id,
        "🤖 Я получил сообщение, но не понял формат.\n\n"
        "Попробуй:\n"
        "Kyiv → Lviv → 2026-06-01"
    )

# -----------------------------
# WEBHOOK ENDPOINT
# -----------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("content-type") != "application/json":
        abort(403)

    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])

    return "OK", 200

# -----------------------------
# HEALTH CHECK
# -----------------------------
@app.route("/")
def index():
    return "Bot is alive", 200

# -----------------------------
# START
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

    print("WEBHOOK SET:", f"{WEBHOOK_URL}/webhook")

    app.run(host="0.0.0.0", port=port)
