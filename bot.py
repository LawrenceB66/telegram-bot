import time
import requests
import os

from signal_logic import classify_signal
from send_alert import send_alert
from state_engine import should_alert

API_KEY = os.getenv("FINNHUB_API_KEY")

TICKERS = [
    "AMC", "GME", "CVNA", "UPST",
    "SOFI", "HOOD", "AFRM", "DKNG",
    "MARA", "RIOT", "COIN",
    "AI", "PLTR",
    "LCID", "RIVN", "NIO", "XPEV"
]

CHECK_INTERVAL = 30


def get_price(symbol):
    try:
        if not API_KEY:
            print("ERROR: FINNHUB_API_KEY not found")
            return None, None

        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"
        res = requests.get(url, timeout=5)
        data = res.json()

        price = float(data.get("c", 0))
        prev_close = float(data.get("pc", 0))

        if price == 0 or prev_close == 0:
            return None, None

        change_pct = ((price - prev_close) / prev_close) * 100

        return price, change_pct

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None, None


def run():
    print("IAL ENGINE LIVE")

    while True:
        for symbol in TICKERS:
            try:
                price, change_pct = get_price(symbol)

                if price is None or change_pct is None:
                    print(f"SKIPPING {symbol} — bad data")
                    continue

                volume = "NORMAL"
                velocity = "NORMAL"

                signal = classify_signal(
                    price,
                    change_pct,
                    volume,
                    velocity
                )

                state = signal.get("state", "UNKNOWN")

                if should_alert(symbol, state):
                    send_alert(symbol, price, change_pct, signal)
                    print(f"SENT CLEAN: {symbol} - {state}")
                else:
                    print(f"NO DUPLICATE: {symbol} - {state}")

            except Exception as e:
                print(f"Error with {symbol}: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run()
