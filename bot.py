# =========================
# IAL BOT ENGINE (STABLE + DISCOVERY)
# =========================

import time
import requests
import os

from signal_logic import classify_signal
from send_alert import send_alert
from state_engine import should_alert
from discovery_engine import build_active_list

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

# 🔒 BASE WATCHLIST (CORE)
BASE_WATCHLIST = [
    "AMC", "GME", "CVNA", "UPST",
    "SOFI", "HOOD", "AFRM", "DKNG",
    "MARA", "RIOT", "COIN",
    "AI", "PLTR",
    "LCID", "RIVN", "NIO", "XPEV"
]

CHECK_INTERVAL = 30


def get_quote(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()

        price = data.get("c", 0)
        prev_close = data.get("pc", 0)

        if price and prev_close:
            change_pct = ((price - prev_close) / prev_close) * 100
        else:
            change_pct = 0

        return {
            "price": float(price),
            "change_pct": float(change_pct),
            "volume": 0  # placeholder (RVOL comes later)
        }

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None


def build_market_data(symbols):
    market_data = {}

    for symbol in symbols:
        data = get_quote(symbol)
        if data:
            market_data[symbol] = data

    return market_data


def run():
    print("IAL ENGINE LIVE")

    while True:
        try:
            # STEP 1 — Build base market snapshot
            base_market_data = build_market_data(BASE_WATCHLIST)

            # STEP 2 — Expand with discovery
            active_list = build_active_list(BASE_WATCHLIST, base_market_data)

            # STEP 3 — Pull full data for active list
            market_data = build_market_data(active_list)

            for symbol, data in market_data.items():
                try:
                    price = data["price"]
                    change_pct = data["change_pct"]
                    volume = data["volume"]

                    # ✅ FIXED — MATCHES signal_logic.py EXPECTATION
                    signal = classify_signal(price, change_pct, volume)

                    if signal is None:
                        continue

                    state = signal.get("state")

                    # 🚫 Prevent duplicate alerts
                    if not should_alert(symbol, state):
                        continue

                    send_alert(symbol, price, change_pct, signal)

                    print(f"Sent: {symbol} — {state}")

                except Exception as e:
                    print(f"Error with {symbol}: {e}")

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    run()
