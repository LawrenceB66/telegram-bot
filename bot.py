# =========================
# IAL BOT (CLEAN ENGINE)
# =========================

import requests
import time
import os
from signal_logic import classify_signal
from state_engine import should_alert

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

WATCHLIST = ["AMC", "GME", "CVNA", "UPST"]

CHECK_INTERVAL = 30


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})


def get_data(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        r = requests.get(url)
        data = r.json()

        price = float(data.get("c", 0))
        percent_change = float(data.get("dp", 0))

        # TEMP volume placeholders (until real RVOL engine)
        volume = float(data.get("v", 0))
        avg_volume = volume if volume > 0 else 1  # prevent divide by zero

        return price, percent_change, volume, avg_volume

    except Exception as e:
        print(f"Error with {symbol}: {e}")
        return None, None, None, None


def get_velocity(percent_change):
    # TEMP velocity logic (placeholder until Phase 2)
    if percent_change >= 8:
        return "EXTREME"
    elif percent_change >= 5:
        return "ACCELERATING"
    elif percent_change >= 3.5:
        return "MODERATE"
    elif percent_change < 2:
        return "REVERSING"
    else:
        return "NORMAL"


def run():
    print("IAL ENGINE LIVE")

    while True:
        for symbol in WATCHLIST:

            price, percent_change, volume, avg_volume = get_data(symbol)

            if price is None:
                continue

            velocity = get_velocity(percent_change)

            signal = classify_signal(
                price,
                percent_change,
                volume,
                avg_volume,
                velocity
            )

            if not signal:
                continue

            state = signal["state"]

            if not should_alert(symbol, state):
                continue

            message = (
                f"{symbol}\n\n"
                f"Price: {price:.2f} • {percent_change:.2f}%\n\n"
                f"{signal['emoji']}\n\n"
                f"Structure:\n"
                f"Volume: {signal['volume']}\n"
                f"Velocity: {signal['velocity']}"
            )

            send_telegram(message)

            print(f"Sent: {symbol} — {state}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run()
