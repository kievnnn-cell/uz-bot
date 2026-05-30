from flask import Blueprint, request
import telebot
import os

from bot import bot

webhook = Blueprint("webhook", __name__)

@webhook.route("/webhook", methods=["POST"])
def hook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200
