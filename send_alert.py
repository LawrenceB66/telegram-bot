=========================

TELEGRAM ALERT SENDER (CLEAN — NO SMART QUOTES)

=========================

import os
import requests

BOT_TOKEN = os.getenv(“TOKEN”)
CHAT_ID = os.getenv(“CHAT_ID”)

def send_alert(symbol, price, change_pct, signal):

try:

    state = signal.get("state", "UNKNOWN")

    volume = signal.get("volume", "N/A")

    velocity = signal.get("velocity", "N/A")



    message = (

        f"#{symbol}\n"

        f"Price: ${price:.2f} • {change_pct:.2f}%\n\n"

        f"{state}\n\n"

        f"Structure:\n"

        f"Volume: {volume}\n"

        f"Velocity: {velocity}"

    )



    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"



    payload = {

        "chat_id": CHAT_ID,

        "text": message

    }



    response = requests.post(url, data=payload, timeout=5)



    print("---- TELEGRAM DEBUG ----")

    print(f"Status Code: {response.status_code}")

    print(f"Response: {response.text}")

    print("------------------------")



except Exception as e:

    print(f"Send alert error: {e}")
