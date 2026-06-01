import requests
import os

# ✅ MATCH bot.py ENV VARIABLES
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_alert(message):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

        payload = {
            "chat_id": CHAT_ID,
            "text": message
        }

        print("📡 Sending to Telegram...")
        print(f"CHAT_ID: {CHAT_ID}")

        r = requests.post(url, json=payload, timeout=10)

        print("📬 Telegram Response:")
        print(r.text)

    except Exception as e:
        print(f"❌ TELEGRAM ERROR: {e}")
