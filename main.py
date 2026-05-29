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
# IMPORTANT FIX (409 ERROR)
# =========================
bot.remove_webhook()
try:
    bot.stop_polling()
except:
    pass

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
# CALLBACK
# =========================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    s = get_state(chat_id)
    data = call.data

    if data.startswith("from:"):
        s["from"] = data.split(":")[1]
        s["step"] = "to"

        bot.edit_message_text(
            f"
