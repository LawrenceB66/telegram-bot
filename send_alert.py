print("IAL FORCE VERSION 5")

import os

import requests

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

CHAT_ID = os.getenv("CHAT_ID")

def send_alert(symbol, price, change_pct, signal):

    try:

        # HARD PROTECTION — SIGNAL MUST EXIST

        if signal is None:

            print(f"SKIPPING — SIGNAL IS NONE: {symbol}")

            return

        if not BOT_TOKEN or not CHAT_ID:

            print("ERROR: Missing TELEGRAM_TOKEN or CHAT_ID")

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

            f"#{symbol}\n"

            f"Price: ${price_str} | {change_str}%\n\n"

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

        response = requests.post(

            url,

            data=payload,

            timeout=5

        )

        if response.status_code != 200:

            print(

                f"Telegram Error: "

                f"{response.status_code} | "

                f"{response.text}"

            )

    except Exception as e:

        print(f"Send alert error: {e}")
