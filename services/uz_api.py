import threading
import time
import re

def parse_request(text):
    # поезд №81 Киев–Ивано-Франковск, купе

    number = re.search(r"№(\d+)", text)
    seat_type = "купе" if "купе" in text else None

    return {
        "train": number.group(1) if number else None,
        "seat": seat_type
    }


def fake_check_uz(train_number, seat_type):
    # TODO: сюда подключается реальный API УЗ
    # сейчас имитация
    return True  # значит "купе появилось"


def monitor_loop(bot, chat_id, train_number, seat_type):
    while True:
        if fake_check_uz(train_number, seat_type):
            bot.send_message(
                chat_id,
                f"🚨 Есть места!\nПоезд №{train_number}\nТип: {seat_type}"
            )
            break

        time.sleep(60)  # проверка каждую минуту


def start_monitor(bot, chat_id, text):
    data = parse_request(text)

    if not data["train"]:
        bot.send_message(chat_id, "❌ Не понял номер поезда")
        return

    thread = threading.Thread(
        target=monitor_loop,
        args=(bot, chat_id, data["train"], data["seat"])
    )
    thread.start()
