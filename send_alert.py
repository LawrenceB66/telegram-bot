import os
import requests

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def send_alert(symbol, price, change_pct, signal):

    try:

        if signal is None:
            print(f"SKIPPING — SIGNAL IS NONE: {symbol}")
            return

        if not BOT_TOKEN or not CHAT_ID:
            print("ERROR: Missing TELEGRAM_TOKEN or CHAT_ID")
            return

        price_str = f"{float(price):.2f}"
        change_str = f"{float(change_pct):.2f}"

        emoji = signal.get("emoji", "")
        name = signal.get("name", "")
        volume = signal.get("volume", "N/A")
        velocity = signal.get("velocity", "N/A")
        read = signal.get("read", "")

        message = (
            f"#{symbol}\n\n"
            f"Price: ${price_str} • {change_str}%\n\n"
            f"{emoji} {name}\n\n"
            f"Volume: {volume}\n"
            f"Velocity: {velocity}\n\n"
            f"NOTE:\n"
            f"{read}"
        )

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        payload = {
            "chat_id": CHAT_ID,
            "text": message
        }

        response = requests.post(
            url,
            data=payload,
            timeout=10
        )

        if response.status_code == 200:
            print(f"ALERT SENT: {symbol} - {name}")
        else:
            print(
                f"Telegram Error: "
                f"{response.status_code} | "
                f"{response.text}"
            )

    except Exception as e:
        print(f"Send alert error: {e}")
