import requests
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")

CHAT_ID = os.getenv("CHAT_ID")

def send_alert(message):

    try:

        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

        payload = {

            "chat_id": CHAT_ID,

            "text": message

        }

        requests.post(url, json=payload, timeout=10)

    except Exception as e:

        print(f"Telegram Error: {e}")
