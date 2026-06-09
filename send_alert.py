print("IAL FORCE VERSION 5")

import os
import requests

BOT_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_alert(symbol, price, change_pct, signal):

    try:
        # HARD PROTECTION — SIGNAL MUST EXIST
        if signal is None:
            print("SKIPPING — SIGNAL IS NONE:", symbol)
            return

        # SAFE EXTRACTION
        state = str(signal.get("state") or "UNKNOWN")
        volume = str(signal.get("volume") or "N/A")
        velocity = str(signal.get("velocity") or "N/A")

        # SAFE NUMBERS
        price_str = format(price if price is not None else 0, ".2f")
        change_str = format(change_pct if change_pct is not None else 0, ".2f")

        # MESSAGE BUILD
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
