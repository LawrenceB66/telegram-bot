# IAL_CLEAN_v1

import os
import requests

BOT_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_alert(symbol, price, change_pct, signal):

    try:
        state = signal.get("state", "UNKNOWN")
        volume = signal.get("volume", "N/A")
        velocity = signal.get("velocity", "N/A")

        message = (
            "#" + symbol + "\n" +
            "Price: $" + format(price, ".2f") + " | " + format(change_pct, ".2f") + "%\n\n" +
            state + "\n\n" +
            "Structure:\n" +
            "Volume: " + volume + "\n" +
            "Velocity: " + velocity
        )

        url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"

        payload = {
            "chat_id": CHAT_ID,
            "text": message
        }

        response = requests.post(url, data=payload, timeout=5)

        print("TELEGRAM STATUS:", response.status_code)
        print("TELEGRAM RESPONSE:", response.text)

    except Exception as e:
        print("Send alert error:", e)
