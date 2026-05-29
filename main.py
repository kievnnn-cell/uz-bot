import os
import telebot
from flask import Flask, request, abort

# --- ENV VARIABLES ---
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    raise Exception("TOKEN is not set in environment variables")

if not WEBHOOK_URL:
    raise Exception("WEBHOOK_URL is not set in environment variables")

# --- BOT ---
bot = telebot.TeleBot(TOKEN, threaded=False)

# --- FLASK APP ---
app = Flask(__name__)

print("BOT STARTED")
print("WEBHOOK BASE:", WEBHOOK_URL)

# --- TEST COMMAND ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Бот работает через webhook 🚀")

# --- WEBHOOK ENDPOINT (фиксированный путь) ---
@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get('content-type') != 'application/json':
        abort(403)

    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])

    return "OK", 200

# --- HEALTH CHECK (Render) ---
@app.route("/")
def index():
    return "Bot is alive", 200


# --- START SERVER ---
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))

    # чистим старые webhook (очень важно)
    bot.remove_webhook()

    # ставим новый webhook
    bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

    print("WEBHOOK SET:", f"{WEBHOOK_URL}/webhook")

    # запуск Flask
    app.run(host="0.0.0.0", port=PORT)
