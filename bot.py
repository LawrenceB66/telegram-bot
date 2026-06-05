# =========================
# IAL MAIN BOT (FIXED)
# =========================

import time
import requests
from signal_logic import process_signal
from state_engine import should_alert

FINNHUB_API_KEY = "YOUR_API_KEY"
TELEGRAM_TOKEN = "YOUR_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

WATCHLIST = ["AMC", "GME", "CVNA", "UPST"]

CHECK_INTERVAL = 30


def get_price_data(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    data = response.json()

    price = float(data.get("c", 0))
    prev_close = float(data.get("pc", 0))

    if prev_close == 0:
        return None

    percent_change = ((price - prev_close) / prev_close) * 100

    return price, percent_change


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=payload)


def format_message(symbol, price, percent, emoji, volume, velocity):
    return f"""{symbol}

Price: {price:.2f} • {percent:.2f}%

{emoji}

Structure:
Volume: {volume}
Velocity: {velocity}
"""


def run():
    print("IAL ENGINE LIVE")

    while True:
        for symbol in WATCHLIST:
            try:
                data = get_price_data(symbol)

                if not data:
                    continue

                price, percent_change = data

                # 🔥 TEMP PLACEHOLDERS (until velocity engine built)
                volume = "ELEVATED" if abs(percent_change) >= 3.5 else "NORMAL"
                velocity = "ACCELERATING" if abs(percent_change) >= 5 else "BUILDING"

                signal = process_signal(symbol, percent_change, volume, velocity)

                if not signal:
                    continue

                if should_alert(symbol, signal["state"]):
                    message = format_message(
                        symbol,
                        price,
                        percent_change,
                        signal["emoji"],
                        signal["volume"],
                        signal["velocity"]
                    )

                    send_telegram(message)
                    print(f"Sent: {symbol} — {signal['state']}")

            except Exception as e:
                print(f"Error with {symbol}: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run()
