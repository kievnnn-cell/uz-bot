import os
import logging
import httpx
from datetime import datetime, timedelta

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


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "🚆 Введи маршрут:\n"
        "пример: Киев–Ивано-Франковск"
    )


# ---------------- ROUTE PARSER ----------------
def parse_route(text: str):
    parts = text.split("–")
    if len(parts) < 2:
        return None, None
    return parts[0].strip(), parts[1].strip()


# ---------------- STEP 1: ROUTE ----------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    frm, to = parse_route(update.message.text)

    if not frm or not to:
        await update.message.reply_text("❌ Формат: Киев–Ивано-Франковск")
        return

    context.user_data["from"] = frm
    context.user_data["to"] = to

    keyboard = [
        [InlineKeyboardButton("📅 Сегодня", callback_data="date_0")],
        [InlineKeyboardButton("📅 Завтра", callback_data="date_1")],
        [InlineKeyboardButton("📅 +2 дня", callback_data="date_2")],
    ]

    await update.message.reply_text(
        "Выбери дату:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------------- DATE ----------------
def get_date(offset: int):
    return (datetime.now() + timedelta(days=offset)).strftime("%d.%m.%Y")


# ---------------- STEP 2: DATE ----------------
async def date_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    offset = int(q.data.split("_")[1])
    context.user_data["date"] = get_date(offset)

    await q.edit_message_text("🔎 Ищу поезда...")

    await search_trains(q, context.user_data)


# ---------------- UZ SEARCH ----------------
async def search_trains(query, state):
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                "https://booking.uz.gov.ua/en/purchase/search/",
                data={
                    "from": state["from"],
                    "to": state["to"],
                    "date": state["date"],
                },
            )
    except Exception as e:
        logger.error(f"UZ ERROR: {e}")
        await query.message.reply_text("❌ Ошибка подключения к УЗ")
        return

    data = r.json()

    if "value" not in data:
        await query.message.reply_text("❌ Нет данных УЗ")
        return

    trains = data["value"][:5]

    keyboard = [
        [InlineKeyboardButton(f"🚆 №{t.get('num')}", callback_data=f"train_{t.get('num')}")]
        for t in trains
    ]

    context = query.application
    query.application.bot_data["trains"] = trains

    await query.message.reply_text(
        "Выбери поезд:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------------- STEP 3: TRAIN ----------------
async def train_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    train_num = q.data.split("_")[1]
    context.user_data["train"] = train_num

    keyboard = [
        [InlineKeyboardButton("🚇 Купе", callback_data="wagon_coupe")],
        [InlineKeyboardButton("🪑 Плацкарт", callback_data="wagon_plats")],
    ]

    await q.edit_message_text(
        f"Поезд №{train_num}\nВыбери тип вагона:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------------- STEP 4: WAGON ----------------
async def wagon_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    wagon = "купе" if q.data == "wagon_coupe" else "плацкарт"
    context.user_data["wagon"] = wagon

    await q.edit_message_text("🔎 Получаю данные...")

    await final_result(q, context.user_data)


# ---------------- FINAL RESULT ----------------
async def final_result(query, state):
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                "https://booking.uz.gov.ua/en/purchase/search/",
                data={
                    "from": state["from"],
                    "to": state["to"],
                    "date": state["date"],
                },
            )
    except Exception as e:
        logger.error(f"UZ FINAL ERROR: {e}")
        await query.message.reply_text("❌ Ошибка УЗ")
        return

    data = r.json()

    if "value" not in data:
        await query.message.reply_text("❌ Нет данных")
        return

    msg = "🚆 Результат:\n\n"
    found = False

    for t in data["value"]:
        if str(t.get("num")) != state.get("train"):
            continue

        found = True
        msg += f"🚆 Поезд №{t.get('num')}\n"
        msg += f"{t.get('from')} → {t.get('to')}\n\n"

        for tp in t.get("types", []):
            if state["wagon"] not in tp.get("title", "").lower():
                continue

            msg += f"• {tp.get('title')}: {tp.get('places')}\n"

    if not found:
        msg = "❌ Поезд не найден"

    await query.message.reply_text(msg)


# ---------------- WEBHOOK ----------------
async def post_init(app: Application):
    url = f"{BASE_URL}{WEBHOOK_PATH}"

    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.bot.set_webhook(url=url)

    logger.info(f"Webhook set: {url}")


app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(CallbackQueryHandler(date_cb, pattern="date_"))
app.add_handler(CallbackQueryHandler(train_cb, pattern="train_"))
app.add_handler(CallbackQueryHandler(wagon_cb, pattern="wagon_"))

app.post_init = post_init


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=f"{BASE_URL}{WEBHOOK_PATH}",
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )
