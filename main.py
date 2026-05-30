import os
from flask import Flask, request
import telebot

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    raise Exception("BOT_TOKEN is not set in environment variables")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

app = Flask(__name__)

# =========================
# STATES (простая память)
# =========================
user_state = {}

STATE_ROUTE = "route_input"


# =========================
# START
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_state[user_id] = None

    bot.send_message(
        user_id,
        "Привет! Я бот поиска маршрутов 🚆\n"
        "Выбери действие:\n\n"
        "➡ /route — найти маршрут"
    )


# =========================
# ROUTE COMMAND
# =========================
@bot.message_handler(commands=['route'])
def route_start(message):
    user_id = message.chat.id
    user_state[user_id] = STATE_ROUTE

    bot.send_message(
        user_id,
        "Введите маршрут:\n"
        "Формат:\nKyiv → Lviv → 2026-06-01"
    )


# =========================
# TEXT HANDLER (STATE MACHINE)
# =========================
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.chat.id
    text = message.text.strip()

    state = user_state.get(user_id)

    if state == STATE_ROUTE:
        user_state[user_id] = None

        try:
            parts = text.split("→")
            if len(parts) != 3:
                raise ValueError()

            from_city = parts[0].strip()
            to_city = parts[1].strip()
            date = parts[2].strip()

            bot.send_message(
                user_id,
                f"🔎 Ищу маршрут:\n"
                f"{from_city} → {to_city}\n"
                f"📅 Дата: {date}\n\n"
                f"✅ (заглушка поиска — дальше подключим API)"
            )

        except:
            bot.send_message(
                user_id,
                "❌ Неверный формат!\n"
                "Пример:\nKyiv → Lviv → 2026-06-01"
            )
        return

    bot.send_message(user_id, "Нажми /route чтобы начать поиск маршрута")


# =========================
# WEBHOOK SETUP
# =========================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


@app.route("/", methods=["GET"])
def index():
    return "Bot is running", 200


# =========================
# START SERVER
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    print("BOT STARTED")

    if WEBHOOK_URL:
        full_webhook = f"{WEBHOOK_URL}/{TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=full_webhook)
        print("WEBHOOK SET:", full_webhook)

    app.run(host="0.0.0.0", port=port)
