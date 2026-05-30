import telebot
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

from services.uz_api import start_monitor

@bot.message_handler(func=lambda m: True)
def handle(message):
    text = message.text.lower()

    # пример команды
    if "поезд" in text:
        start_monitor(bot, message.chat.id, text)
        bot.send_message(message.chat.id, "📡 Мониторинг запущен")
