import requests
import json


def check_whatsapp_exists(waInstance, apiTokenInstance, phone_number):
    url = f"https://7103.api.greenapi.com/waInstance{waInstance}/checkWhatsapp/{apiTokenInstance}"
    payload = {"phoneNumber": phone_number}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data.get("existsWhatsapp", False)

    return False


def send_message(waInstance, apiTokenInstance, phone_number, msg):
    url = f"https://7103.api.greenapi.com/waInstance{waInstance}/sendMessage/{apiTokenInstance}"

    payload = {"chatId": f"{phone_number}@c.us", "message": f"{msg}"}
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)

    # print(response.text.encode("utf8"))
    return response.status_code
