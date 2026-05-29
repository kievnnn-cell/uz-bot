import os
import telebot
from flask import Flask, request

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

print("BOT STARTED")

# --- тест команда ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Бот работает через webhook 🚀")

# --- webhook endpoint ---
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


# --- health check (Render любит это) ---
@app.route("/")
def index():
    return "Bot is alive", 200


if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))

    # webhook URL (ВАЖНО: Render URL)
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")

    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

    app.run(host="0.0.0.0", port=PORT)
