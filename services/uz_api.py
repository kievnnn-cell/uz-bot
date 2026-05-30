import requests
import logging

BASE_URL = "https://app.uz.gov.ua/api"  # публичный backend слой (используется мобильным клиентом)

def get_train_info(train_number, from_city, to_city):
    """
    Получаем данные по поезду через публичный API слой УЗ.
    """

    try:
        url = f"{BASE_URL}/search"
        params = {
            "query": f"{from_city} {to_city}",
        }

        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        return data

    except Exception as e:
        logging.error(f"UZ API error: {e}")
        return None


def check_coupe_available(train_number, from_city, to_city):
    """
    Проверяем наличие купе.
    """

    data = get_train_info(train_number, from_city, to_city)

    if not data:
        return False

    try:
        for train in data.get("trains", []):
            if str(train.get("number")) == str(train_number):

                for wagon in train.get("wagons", []):
                    if wagon.get("type") in ["coupe", "КОМФ", "coupe_car"]:
                        if wagon.get("available_seats", 0) > 0:
                            return True

        return False

    except Exception as e:
        logging.error(f"Parse error: {e}")
        return False
