import os
import time
import telebot
from flask import Flask, request

TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# ---------------- DEBUG WEBHOOK ----------------
def fix_webhook():
    url = f"{WEBHOOK_URL}/{TOKEN}"

    try:
        info = bot.get_webhook_info()
        print("CURRENT WEBHOOK:", info.url)

        if info.url != url:
            print("FIXING WEBHOOK...")
            bot.remove_webhook()
            time.sleep(1)
            bot.set_webhook(url=url)

        print("WEBHOOK OK:", url)

    except Exception as e:
        print("WEBHOOK ERROR:", e)

# ---------------- START ----------------
user_state = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🚆 Бот живой. Введите маршрут:\nKyiv → Lviv → 2026-06-01"
    )

@bot.message_handler(content_types=['text'])
def text(message):
    bot.send_message(message.chat.id, "Получено: " + message.text)

# ---------------- WEBHOOK ----------------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK"

@app.route("/")
def home():
    return "OK"

# ---------------- START SERVER ----------------
if __name__ == "__main__":
    print("BOT STARTED")

    # 💥 ключевой момент — перед стартом всегда чинит webhook
    fix_webhook()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)import os
import time
import telebot
from telebot import types
from flask import Flask, request

# ---------------- CONFIG ----------------
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    raise Exception("TOKEN is not set in environment variables")

if not WEBHOOK_URL:
    raise Exception("WEBHOOK_URL is not set in environment variables")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# ---------------- SIMPLE STATE ----------------
user_state = {}

# ---------------- WEBHOOK SAFE SETUP ----------------
def set_webhook():
    url = f"{WEBHOOK_URL}/{TOKEN}"

    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=url)
        print("WEBHOOK SET:", url)
    except Exception as e:
        print("WEBHOOK ERROR:", e)

# ---------------- START ----------------
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id

    user_state[chat_id] = "waiting_route"

    bot.send_message(
        chat_id,
        "🚆 Привет! Я бот поиска маршрутов\n\n"
        "Введите маршрут:\n"
        "Kyiv → Lviv → 2026-06-01"
    )

# ---------------- TEXT HANDLER ----------------
@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    state = user_state.get(chat_id)

    # STEP 1: ждём маршрут
    if state == "waiting_route":

        parts = [p.strip() for p in text.split("→")]

        if len(parts) != 3:
            bot.send_message(chat_id, "❌ Формат: Kyiv → Lviv → 2026-06-01")
            return

        from_city, to_city, date = parts

        user_state[chat_id] = {
            "step": "ready",
            "from": from_city,
            "to": to_city,
            "date": date
        }

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔍 Найти билеты", callback_data="search"))
        markup.add(types.InlineKeyboardButton("📅 Расписание", callback_data="schedule"))
        markup.add(types.InlineKeyboardButton("🔄 Новый маршрут", callback_data="reset"))

        bot.send_message(
            chat_id,
            f"🚆 Маршрут принят:\n"
            f"📍 {from_city} → {to_city}\n"
            f"📅 {date}\n\n"
            "Выберите действие:",
            reply_markup=markup
        )

# ---------------- CALLBACK BUTTONS ----------------
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    data = call.data

    state = user_state.get(chat_id, {})

    if data == "search":
        bot.send_message(
            chat_id,
            f"🔎 Ищу билеты...\n"
            f"{state.get('from')} → {state.get('to')}\n"
            f"📅 {state.get('date')}"
        )

    elif data == "schedule":
        bot.send_message(chat_id, "📅 Расписание (пока заглушка)")

    elif data == "reset":
        user_state[chat_id] = "waiting_route"
        bot.send_message(chat_id, "Введите новый маршрут:\nKyiv → Lviv → 2026-06-01")

    bot.answer_callback_query(call.id)

# ---------------- FLASK WEBHOOK ----------------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Bot is alive", 200

# ---------------- START APP ----------------
if __name__ == "__main__":
    print("BOT STARTED")

    set_webhook()

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
