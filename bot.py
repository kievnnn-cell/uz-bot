import telebot
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: True)
def handle(message):
    bot.send_message(message.chat.id, f"📩 Получено: {message.text}")
