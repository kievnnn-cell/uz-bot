import requests
import time
import threading
import re

BASE_URL = "https://booking.uz.gov.ua/api"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json"
}

# ---------------------------
# 1. Поиск станций
# ---------------------------
def search_station(name):
    r = requests.post(
        f"{BASE_URL}/stations/",
        json={"term": name},
        headers=HEADERS,
        timeout=15
    )
    data = r.json()
    return data.get("data", [])

# ---------------------------
# 2. Поиск рейса
# ---------------------------
def get_trains(from_id, to_id, date):
    r = requests.post(
        f"{BASE_URL}/schedule/",
        json={
            "from": from_id,
            "to": to_id,
            "date": date
        },
        headers=HEADERS,
        timeout=15
    )
    return r.json()

# ---------------------------
# 3. Проверка купе
# ---------------------------
def check_berths(train_data, train_number):
    for train in train_data.get("data", {}).get("list", []):
        if str(train.get("num")) == str(train_number):
            for wagon in train.get("types", []):
                if wagon.get("type") == "compartment":
                    return wagon.get("places", 0) > 0
    return False

# ---------------------------
# 4. МОНИТОР
# ---------------------------
def monitor(bot, chat_id, from_city, to_city, train_number, seat_type="compartment"):
    from_station = search_station(from_city)[0]["value"]
    to_station = search_station(to_city)[0]["value"]

    date = time.strftime("%d.%m.%Y")

    while True:
        try:
            data = get_trains(from_station, to_station, date)

            available = check_berths(data, train_number)

            if available:
                bot.send_message(
                    chat_id,
                    f"🚨 БИЛЕТЫ НАЙДЕНЫ!\n"
                    f"Поезд №{train_number}\n"
                    f"Купе доступно 🎟"
                )
                break

        except Exception as e:
            print("ERROR:", e)

        time.sleep(60)

# ---------------------------
# 5. СТАРТ МОНИТОРА
# ---------------------------
def start_monitor(bot, chat_id, text):
    match = re.search(r"№(\d+)", text)

    if not match:
        bot.send_message(chat_id, "❌ Не найден номер поезда")
        return

    train_number = match.group(1)

    # фиксированный парсинг маршрута
    parts = text.split(" ")
    route = text.split("Киев–Ивано-Франковск")  # упрощённо

    thread = threading.Thread(
        target=monitor,
        args=(bot, chat_id, "Киев", "Ивано-Франковск", train_number)
    )
    thread.start()
