import os
import logging
from flask import Flask, request

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
BASE_URL = os.getenv("BASE_URL")

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# ===== BOT INIT =====
application = Application.builder().token(BOT_TOKEN).build()


# ===== SIMPLE COMMAND =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚆 Монитор УЗ активен")


# ===== PARSER COMMAND =====
async def parse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    # пример: "поезд №81 Киев–Ивано-Франковск, купе"
    if "купе" in text:
        await update.message.reply_text("🔎 Ищу купе по указанному поезду...")
    else:
        await update.message.reply_text("Формат: поезд №81 Киев–Ивано-Франковск, купе")


application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, parse))


# ===== FLASK WEBHOOK =====
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    application.update_queue.put_nowait(update)
    return "ok"


@app.route("/")
def home():
    return "BOT RUNNING"


# ===== STARTUP =====
if __name__ == "__main__":
    import asyncio

    async def run():
        await application.initialize()
        await application.start()

        webhook_url = BASE_URL + WEBHOOK_PATH
        await application.bot.set_webhook(webhook_url)

        logging.info(f"Webhook set: {webhook_url}")

        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

    asyncio.run(run())
