import os
import telebot
from flask import Flask, request
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

print("BOT STARTING...")

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    raise Exception("BOT_TOKEN missing")

if not WEBHOOK_URL:
    raise Exception("WEBHOOK_URL missing")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ======================
# SIMPLE STATE STORAGE (in-memory)
# ======================
user_state = {}

# ======================
# WEBHOOK SETUP
# ======================
bot.remove_webhook()
bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

print("WEBHOOK SET:", WEBHOOK_URL)


# ======================
# MAIN MENU
# ======================
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🚆 Найти маршрут"))
    markup.add(KeyboardButton("📍 Мои поездки"))
    markup.add(KeyboardButton("ℹ️ Помощь"))
    return markup


# ======================
# START
# ======================
@bot.message_handler(commands=['start'])
def start(message):
    user_state[message.chat.id] = {}
    bot.send_message(
        message.chat.id,
        "Привет! Я бот поиска маршрутов 🚆\nВыбери действие:",
        reply_markup=main_menu()
    )


# ======================
# BUTTON HANDLER
# ======================
@bot.message_handler(func=lambda m: True)
def router(message):
    chat_id = message.chat.id
    text = message.text

    state = user_state.get(chat_id, {})

    # ------------------
    # START ROUTE FLOW
    # ------------------
    if text == "🚆 Найти маршрут":
        user_state[chat_id] = {"step": "from"}
        bot.send_message(chat_id, "📍 Введи город отправления:")
        return

    # ------------------
    # STEP 1: FROM
    # ------------------
    if state.get("step") == "from":
        state["from"] = text
        state["step"] = "to"
        user_state[chat_id] = state

        bot.send_message(chat_id, "📍 Введи город назначения:")
        return

    # ------------------
    # STEP 2: TO
    # ------------------
    if state.get("step") == "to":
        state["to"] = text
        state["step"] = "date"
        user_state[chat_id] = state

        bot.send_message(chat_id, "📅 Введи дату (YYYY-MM-DD):")
        return

    # ------------------
    # STEP 3: DATE
    # ------------------
    if state.get("step") == "date":
        state["date"] = text

        result = f"""
🚆 Маршрут найден:

📍 Откуда: {state['from']}
📍 Куда: {state['to']}
📅 Дата: {state['date']}

✔ Идёт поиск билетов...
"""

        bot.send_message(chat_id, result, reply_markup=main_menu())

        # reset state
        user_state[chat_id] = {}
        return

    # ------------------
    # DEFAULT
    # ------------------
    bot.send_message(chat_id, "Выбери действие из меню 👇", reply_markup=main_menu())


# ======================
# WEBHOOK
# ======================
@app.route("/webhook", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(
        request.stream.read().decode("utf-8")
    )
    bot.process_new_updates([update])
    return "OK", 200


@app.route("/", methods=["GET"])
def home():
    return "BOT IS RUNNING", 200


# ======================
# RUN
# ======================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
