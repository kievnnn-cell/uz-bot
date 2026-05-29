```python
import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# =========================
# TOKEN FROM RENDER
# =========================
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise Exception("TOKEN is not set in environment variables")

bot = telebot.TeleBot(TOKEN)

# =========================
# USER STATE
# =========================
user_state = {}

def get_state(chat_id):
    if chat_id not in user_state:
        user_state[chat_id] = {
            "step": "from",
            "from": None,
            "to": None,
            "date": None
        }

    return user_state[chat_id]

# =========================
# KEYBOARDS
# =========================
def from_keyboard():
    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton("Kyiv", callback_data="from:Kyiv"),
        InlineKeyboardButton("Lviv", callback_data="from:Lviv")
    )

    return kb


def to_keyboard():
    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton("Kyiv", callback_data="to:Kyiv"),
        InlineKeyboardButton("Lviv", callback_data="to:Lviv")
    )

    kb.add(
        InlineKeyboardButton("↔️ Swap", callback_data="swap")
    )

    return kb

# =========================
# START
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    s = get_state(message.chat.id)

    s["step"] = "from"

    bot.send_message(
        message.chat.id,
        "🚆 Выбери FROM:",
        reply_markup=from_keyboard()
    )

# =========================
# CALLBACKS
# =========================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    s = get_state(chat_id)

    data = call.data

    # FROM
    if data.startswith("from:"):
        s["from"] = data.split(":")[1]
        s["step"] = "to"

        bot.edit_message_text(
            f"FROM: {s['from']}\n\nВыбери TO:",
            chat_id,
            call.message.message_id,
            reply_markup=to_keyboard()
        )

    # TO
    elif data.startswith("to:"):
        s["to"] = data.split(":")[1]
        s["step"] = "date"

        bot.edit_message_text(
            f"🚆 {s['from']} → {s['to']}\n\n📅 Введи дату:",
            chat_id,
            call.message.message_id
        )

    # SWAP
    elif data == "swap":
        s["from"], s["to"] = s["to"], s["from"]

        bot.answer_callback_query(
            call.id,
            "Маршрут изменён"
        )

        bot.edit_message_text(
            f"🔄 {s['from']} → {s['to']}",
            chat_id,
            call.message.message_id,
            reply_markup=to_keyboard()
        )

# =========================
# DATE INPUT
# =========================
@bot.message_handler(func=lambda m: True)
def text_handler(message):
    s = get_state(message.chat.id)

    if s["step"] == "date":
        s["date"] = message.text

        bot.send_message(
            message.chat.id,
            f"🚆 SEARCH STARTED\n\n"
            f"FROM: {s['from']}\n"
            f"TO: {s['to']}\n"
            f"DATE: {s['date']}"
        )

# =========================
# RUN
# =========================
if __name__ == "__main__":
    print("BOT STARTED 🚆")

    # remove old webhook
    bot.remove_webhook()

    # stable polling for Render
    bot.infinity_polling(
        timeout=30,
        long_polling_timeout=30
    )
```
