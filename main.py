import os
import telebot
from flask import Flask, request

# ======================
# ENV VARIABLES (Render)
# ======================
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    raise Exception("TOKEN is not set in environment variables")

if not WEBHOOK_URL:
    raise Exception("WEBHOOK_URL is not set in environment variables")

# ======================
# BOT + SERVER
# ======================
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

print("BOT STARTED")

# ======================
# START COMMAND
# ======================
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup()

    btn1 = telebot.types.InlineKeyboardButton("🚆 Найти билеты", callback_data="find")
    btn2 = telebot.types.InlineKeyboardButton("ℹ️ Помощь", callback_data="help")

    markup.add(btn1, btn2)

    bot.send_message(
        message.chat.id,
        "Привет! Я бот поиска маршрутов 🚆\nВыбери действие:",
        reply_markup=markup
    )

# ======================
# CALLBACK HANDLER
# ======================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):

    if call.data == "find":
        bot.send_message(call.message.chat.id, "Введите маршрут:\nФормат: Kyiv → Lviv → 2026-06-01")

    elif call.data == "help":
        bot.send_message(call.message.chat.id, "Я помогу найти маршрут и билеты 🚆")

# ======================
# TEXT PARSER (простая логика маршрута)
# ======================
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text

    if "→" in text:
        try:
            parts = [x.strip() for x in text.split("→")]

            if len(parts) == 3:
                origin = parts[0]
                destination = parts[1]
                date = parts[2]

                bot.send_message(
                    message.chat.id,
                    f"🚆 Маршрут принят:\n📍 Откуда: {origin}\n📍 Куда: {destination}\n📅 Дата: {date}\n\n🔎 Ищу варианты..."
                )

                # сюда позже подключим API/поиск

            else:
                bot.send_message(message.chat.id, "Формат: Kyiv → Lviv → 2026-06-01")

        except Exception:
            bot.send_message(message.chat.id, "Ошибка обработки маршрута")

# ======================
# WEBHOOK ENDPOINT
# ======================
@app.route("/webhook", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# ======================
# HEALTH CHECK (Render)
# ======================
@app.route("/")
def index():
    return "Bot is alive", 200

# ======================
# START APP
# ======================
if __name__ == "__main__":

    PORT = int(os.environ.get("PORT", 5000))

    # важно: всегда чистим старый webhook
    bot.remove_webhook()

    # ставим новый webhook
    bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

    print("WEBHOOK SET:", f"{WEBHOOK_URL}/webhook")

    app.run(host="0.0.0.0", port=PORT)
