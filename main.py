import os
import telebot
from flask import Flask, request

# =====================
# CONFIG
# =====================

TOKEN = os.getenv("BOT_TOKEN")  # <- В Render добавляешь BOT_TOKEN
WEBHOOK_HOST = os.getenv("WEBHOOK_URL")  # например: https://your-app.onrender.com

if not TOKEN:
    raise Exception("BOT_TOKEN is not set in environment variables")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

# =====================
# SIMPLE STATE STORAGE (v2 FSM)
# =====================

user_state = {}

STATE_START = "start"
STATE_ROUTE = "route_input"

# =====================
# START COMMAND
# =====================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_state[user_id] = STATE_START

    bot.send_message(
        user_id,
        "Привет! Я бот поиска маршрутов 🚆\nВыбери действие:"
    )

# =====================
# TEXT HANDLER (STATE MACHINE)
# =====================

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.chat.id
    text = message.text.strip()

    state = user_state.get(user_id, STATE_START)

    # ---- START STATE ----
    if state == STATE_START:
        if "маршрут" in text.lower() or "поиск" in text.lower():
            user_state[user_id] = STATE_ROUTE
            bot.send_message(user_id, "Введите маршрут:\nФормат: Kyiv → Lviv → 2026-06-01")
        else:
            bot.send_message(user_id, "Нажмите /start и выберите действие 🚆")
        return

    # ---- ROUTE INPUT STATE ----
    if state == STATE_ROUTE:
        try:
            parts = text.split("→")

            if len(parts) != 3:
                bot.send_message(user_id, "❌ Неверный формат!\nПример: Kyiv → Lviv → 2026-06-01")
                return

            from_city = parts[0].strip()
            to_city = parts[1].strip()
            date = parts[2].strip()

            # reset state
            user_state[user_id] = STATE_START

            bot.send_message(
                user_id,
                f"🔎 Ищу маршрут...\n\n"
                f"🚆 {from_city} → {to_city}\n📅 {date}\n\n"
                f"✔️ (тут позже будет API поиск)"
            )

        except Exception as e:
            bot.send_message(user_id, f"Ошибка обработки: {e}")

# =====================
# WEBHOOK ROUTE
# =====================

@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# =====================
# HEALTH CHECK
# =====================

@app.route('/', methods=['GET'])
def index():
    return "BOT IS RUNNING", 200

# =====================
# START APP
# =====================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    webhook_url = f"{WEBHOOK_HOST}/webhook"

    print("BOT STARTED")
    print("WEBHOOK:", webhook_url)

    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)

    app.run(host="0.0.0.0", port=port)
