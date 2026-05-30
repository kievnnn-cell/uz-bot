import os
import re
import telebot
from telebot import types
from flask import Flask, request, abort

# ==================================
# ENVIRONMENT
# ==================================

TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    raise Exception("TOKEN is not set")

if not WEBHOOK_URL:
    raise Exception("WEBHOOK_URL is not set")

# ==================================
# BOT
# ==================================

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

print("BOT STARTED")
print("WEBHOOK BASE:", WEBHOOK_URL)

# ==================================
# START COMMAND
# ==================================

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🚆 Добро пожаловать!\n\n"
        "Введите маршрут в формате:\n"
        "Kyiv → Lviv → 2026-06-01"
    )

# ==================================
# TEXT HANDLER
# ==================================

@bot.message_handler(content_types=['text'])
def handle_text(message):

    text = message.text.strip()

    print("MESSAGE:", text)

    match = re.search(
        r"(.+?)\s*→\s*(.+?)\s*→\s*(\d{4}-\d{2}-\d{2})",
        text
    )

    if match:

        from_city = match.group(1).strip()
        to_city = match.group(2).strip()
        date = match.group(3).strip()

        markup = types.InlineKeyboardMarkup()

        btn1 = types.InlineKeyboardButton(
            "🔎 Найти поезда",
            callback_data="find_trains"
        )

        btn2 = types.InlineKeyboardButton(
            "📅 Расписание",
            callback_data="schedule"
        )

        btn3 = types.InlineKeyboardButton(
            "🔄 Новый маршрут",
            callback_data="new_route"
        )

        markup.add(btn1)
        markup.add(btn2)
        markup.add(btn3)

        bot.send_message(
            message.chat.id,
            f"🚆 Маршрут принят\n\n"
            f"📍 Откуда: {from_city}\n"
            f"📍 Куда: {to_city}\n"
            f"📅 Дата: {date}\n\n"
            f"Выберите действие:",
            reply_markup=markup
        )

        return

    bot.send_message(
        message.chat.id,
        "🤖 Не понял формат.\n\n"
        "Пример:\n"
        "Kyiv → Lviv → 2026-06-01"
    )

# ==================================
# BUTTONS
# ==================================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):

    if call.data == "find_trains":

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "🚆 Доступные поезда\n\n"
            "001К Интерсити\n"
            "07:15 → 12:40\n\n"
            "743Л Экспресс\n"
            "10:20 → 15:50\n\n"
            "091Н Ночной\n"
            "22:10 → 06:30"
        )

    elif call.data == "schedule":

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "📅 Раздел расписания находится в разработке."
        )

    elif call.data == "new_route":

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "Введите новый маршрут:\n\n"
            "Kyiv → Lviv → 2026-06-01"
        )

# ==================================
# WEBHOOK
# ==================================

@app.route("/webhook", methods=["POST"])
def webhook():

    if request.headers.get("content-type") != "application/json":
        abort(403)

    json_string = request.get_data().decode("utf-8")

    update = telebot.types.Update.de_json(json_string)

    bot.process_new_updates([update])

    return "OK", 200

# ==================================
# HEALTH CHECK
# ==================================

@app.route("/")
def index():
    return "Bot is alive", 200

# ==================================
# MAIN
# ==================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    bot.remove_webhook()

    bot.set_webhook(
        url=f"{WEBHOOK_URL}/webhook"
    )

    print(
        "WEBHOOK SET:",
        f"{WEBHOOK_URL}/webhook"
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
