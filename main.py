import os
import telebot

print("STARTING BOT...")

TOKEN = os.getenv("BOT_TOKEN")

print("TOKEN LOADED:", bool(TOKEN))

if not TOKEN:
    raise Exception("BOT_TOKEN is missing in Render environment variables")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=["start"])
def start(message):
    print("START COMMAND RECEIVED")
    bot.send_message(message.chat.id, "Бот работает 🚆")

print("BOT STARTED - polling now")

bot.infinity_polling(skip_pending=True)
