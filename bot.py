import time
import requests
import os

from signal_logic import classify_signal
from send_alert import send_alert

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
        url = "https://finnhub.io/api/v1/quote?symbol=" + symbol + "&token=" + API_KEY
        res = requests.get(url, timeout=5)
        data = res.json()

        price = data.get("c")
        prev_close = data.get("pc")

        if price is None or prev_close is None or prev_close == 0:
            return None, None

        price = float(price)
        prev_close = float(prev_close)

        change_pct = ((price - prev_close) / prev_close) * 100

        return price, change_pct

    except Exception as e:
        print("Error fetching " + symbol + ":", e)
        return None, None


def run():
    print("IAL ENGINE LIVE")

    while True:
        for symbol in TICKERS:
            try:
                price, change_pct = get_price(symbol)

                # HARD FILTER — NO BAD DATA PASSES
                if price is None or change_pct is None:
                    print("Skipping " + symbol + " due to bad data")
                    continue

                volume = "NORMAL"
                velocity = "NORMAL"

                signal = classify_signal(
                    price,
                    change_pct,
                    volume,
                    velocity
                )

                send_alert(symbol, price, change_pct, signal)

                print("Sent:", symbol, "-", signal.get("state"))

            except Exception as e:
                print("Error with " + symbol + ":", e)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run()
