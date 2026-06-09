print("IAL FORCE VERSION 4")

import os
import requests

BOT_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_alert(symbol, price, change_pct, signal):

    try:
        state = str(signal.get("state") or "UNKNOWN")
        volume = str(signal.get("volume") or "N/A")
        velocity = str(signal.get("velocity") or "N/A")

        price_str = format(price if price is not None else 0, ".2f")
        change_str = format(change_pct if change_pct is not None else 0, ".2f")

        message = (
            "#" + symbol + "\n" +
            "Price: $" + price_str + " | " + change_str + "%\n\n" +
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

        requests.post(url, data=payload, timeout=5)

    except Exception as e:
        print("Send alert error:", e)
