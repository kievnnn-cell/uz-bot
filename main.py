import telebot
from telebot import types
import sqlite3
import time
import threading

TOKEN = "8813064730:AAGLMW9yfAUJQzFxWXLgHo7aRIjaBm9ewx8"
bot = telebot.TeleBot(TOKEN)

# ================= DB =================

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS watches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    train TEXT,
    from_city TEXT,
    to_city TEXT,
    date TEXT
)
""")
conn.commit()

# ================= STATE =================

user_state = {}

CITIES = ["Kyiv", "Lviv", "Odesa", "Kharkiv", "Dnipro"]

# ================= UI =================

def main_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔍 Search trains", callback_data="search"))
    kb.add(types.InlineKeyboardButton("👀 Watches", callback_data="watches"))
    return kb

def cities_kb(step):
    kb = types.InlineKeyboardMarkup()
    for c in CITIES:
        kb.add(types.InlineKeyboardButton(c, callback_data=f"city:{step}:{c}"))
    return kb

def back_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅ Back", callback_data="back"))
    return kb

# ================= START =================

@bot.message_handler(commands=['start'])
def start(m):
    user_state[m.chat.id] = {"step": "idle"}

    bot.send_message(
        m.chat.id,
        "🚆 V8 Wizard UI\nStable flow engine ready",
        reply_markup=main_menu()
    )

# ================= CALLBACK =================

@bot.callback_query_handler(func=lambda c: True)
def callback(call):

    chat_id = call.message.chat.id
    data = call.data

    state = user_state.get(chat_id, {"step": "idle"})

    # -------- SEARCH START --------
    if data == "search":
        state = {"step": "from"}
        user_state[chat_id] = state

        bot.edit_message_text(
            "📍 Select FROM city:",
            chat_id,
            call.message.message_id,
            reply_markup=cities_kb("from")
        )

    # -------- BACK --------
    elif data == "back":
        user_state[chat_id] = {"step": "idle"}

        bot.edit_message_text(
            "🏠 Main menu",
            chat_id,
            call.message.message_id,
            reply_markup=main_menu()
        )

    # -------- CITY SELECT --------
    elif data.startswith("city:"):

        _, step, city = data.split(":")

        state = user_state.get(chat_id, {"step": "idle"})

        # FROM
        if step == "from":

            state["from"] = city
            state["step"] = "to"
            user_state[chat_id] = state

            bot.edit_message_text(
                f"📍 FROM: {city}\n\nSelect TO city:",
                chat_id,
                call.message.message_id,
                reply_markup=cities_kb("to")
            )

        # TO
        elif step == "to":

            if "from" not in state:
                bot.answer_callback_query(call.id, "Start over")
                return

            if city == state["from"]:
                bot.answer_callback_query(call.id, "Choose different city")
                return

            state["to"] = city
            state["step"] = "date"
            user_state[chat_id] = state

            bot.send_message(
                chat_id,
                f"📍 FROM: {state['from']}\n"
                f"📍 TO: {state['to']}\n\n"
                "📅 Send date (YYYY-MM-DD)"
            )

    # -------- WATCH LIST --------
    elif data == "watches":

        cursor.execute("""
            SELECT train, from_city, to_city, date
            FROM watches
            WHERE chat_id=?
        """, (chat_id,))

        rows = cursor.fetchall()

        if not rows:
            bot.answer_callback_query(call.id, "No watches")
            return

        text = "👀 Your watches:\n\n"

        for r in rows:
            text += f"{r[0]} {r[1]} → {r[2]} | {r[3]}\n"

        bot.send_message(chat_id, text)

# ================= DATE INPUT =================

@bot.message_handler(func=lambda m: True)
def handle_text(m):

    chat_id = m.chat.id
    text = m.text.strip()

    if chat_id not in user_state:
        return

    state = user_state[chat_id]

    if state.get("step") != "date":
        return

    # fake trains (stable layer)
    trains = [
        {"num": "741К", "time": "08:30 → 14:45"},
        {"num": "009П", "time": "10:15 → 16:40"},
        {"num": "106Л", "time": "22:10 → 05:55"},
    ]

    msg = f"🚆 {state['from']} → {state['to']}\n📅 {text}\n\n"

    kb = types.InlineKeyboardMarkup()

    for t in trains:
        msg += f"{t['num']} | {t['time']}\n"

        kb.add(
            types.InlineKeyboardButton(
                f"👀 Watch {t['num']}",
                callback_data=f"watch:{t['num']}:{state['from']}:{state['to']}:{text}"
            )
        )

    kb.add(types.InlineKeyboardButton("🏠 Menu", callback_data="back"))

    bot.send_message(chat_id, msg, reply_markup=kb)

    state["step"] = "idle"
    user_state[chat_id] = state

# ================= WATCH =================

@bot.callback_query_handler(func=lambda c: c.data.startswith("watch:"))
def watch(call):

    _, train, f, t, d = call.data.split(":")

    cursor.execute("""
        INSERT INTO watches(chat_id, train, from_city, to_city, date)
        VALUES (?, ?, ?, ?, ?)
    """, (call.message.chat.id, train, f, t, d))

    conn.commit()

    bot.answer_callback_query(call.id, "Watching started 👀")

# ================= ENGINE =================

def engine():
    while True:
        time.sleep(30)

        cursor.execute("SELECT chat_id, train FROM watches")
        rows = cursor.fetchall()

        for chat_id, train in rows:
            if int(time.time()) % 60 == 0:
                bot.send_message(chat_id, f"🚆 V8 monitoring {train}")

threading.Thread(target=engine, daemon=True).start()

print("V8 Wizard UI running 🚆")
bot.infinity_polling()

if __name__ == "__main__":
    print("BOT STARTED")
    bot.infinity_polling()