import os
import logging
import re
import httpx

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ---------------- CONFIG ----------------
TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_PATH = "/webhook"

UZ_API = "https://booking.uz.gov.ua/en"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

app = Application.builder().token(TOKEN).build()

# ---------------- TEMP USER STATE ----------------
USER_STATE = {}


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚆 Отправь запрос:\n"
        "поезд №81 Киев–Ивано-Франковск"
    )


# ---------------- PARSE ----------------
def parse(text: str):
    train_number = None

    m = re.search(r"№\s*(\d+)", text)
    if m:
        train_number = m.group(1)

    route = text.split("№")[-1] if "№" in text else text
    parts = re.split(r"[–-]", route)

    from_city = parts[0].strip() if len(parts) > 1 else None
    to_city = parts[1].split(",")[0].strip() if len(parts) > 1 else None

    return train_number, from_city, to_city


# ---------------- STEP 1: TEXT INPUT ----------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    train, frm, to = parse(text)

    if not frm or not to:
        await update.message.reply_text("❌ Формат: поезд №81 Киев–Ивано-Франковск")
        return

    USER_STATE[user_id] = {
        "train": train,
        "from": frm,
        "to": to,
    }

    keyboard = [
        [InlineKeyboardButton("🚇 Купе", callback_data="wagon_coupe")],
        [InlineKeyboardButton("🪑 Плацкарт", callback_data="wagon_plats")],
    ]

    await update.message.reply_text(
        "Выбери тип вагона:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------------- STEP 2: WAGON ----------------
async def wagon_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    state = USER_STATE.get(user_id, {})

    wagon = "купе" if query.data == "wagon_coupe" else "плацкарт"
    state["wagon"] = wagon

    USER_STATE[user_id] = state

    keyboard = [
        [InlineKeyboardButton("📅 Сегодня", callback_data="date_today")],
        [InlineKeyboardButton("📅 Завтра", callback_data="date_tomorrow")],
    ]

    await query.edit_message_text(
        f"Выбрано: {wagon}\nТеперь выбери дату:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------------- STEP 3: DATE ----------------
def get_date(option):
    from datetime import datetime, timedelta

    if option == "today":
        return datetime.now().strftime("%d.%m.%Y")
    if option == "tomorrow":
        return (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")


async def date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    state = USER_STATE.get(user_id, {})

    date = get_date("today" if query.data == "date_today" else "tomorrow")
    state["date"] = date

    USER_STATE[user_id] = state

    await query.edit_message_text("🔎 Ищу билеты...")

    await search_and_send(query, state)


# ---------------- UZ SEARCH ----------------
async def search_and_send(query, state):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            "https://booking.uz.gov.ua/en/purchase/search/",
            data={
                "from": state["from"],
                "to": state["to"],
                "date": state["date"],
            },
        )

    data = r.json()

    if "value" not in data:
        await query.message.reply_text("❌ Нет данных УЗ")
        return

    train_filter = state.get("train")
    wagon_filter = state.get("wagon")

    msg = "🚆 Результаты:\n\n"
    found = False

    for t in data["value"]:
        num = str(t.get("num"))

        if train_filter and num != train_filter:
            continue

        found = True
        msg += f"🚆 Поезд №{num}\n"
        msg += f"{t.get('from')} → {t.get('to')}\n"

        if "types" in t:
            for tp in t["types"]:
                title = tp.get("title", "").lower()

                if wagon_filter and wagon_filter not in title:
                    continue

                msg += f"  • {tp.get('title')}: {tp.get('places')}\n"

        msg += "\n"

    if not found:
        msg = "❌ Ничего не найдено"

    await query.message.reply_text(msg)


# ---------------- WEBHOOK ----------------
async def post_init(app: Application):
    url = f"{BASE_URL}{WEBHOOK_PATH}"
    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.bot.set_webhook(url=url)


app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(CallbackQueryHandler(wagon_callback, pattern="wagon_"))
app.add_handler(CallbackQueryHandler(date_callback, pattern="date_"))

app.post_init = post_init


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=f"{BASE_URL}{WEBHOOK_PATH}",
    )
