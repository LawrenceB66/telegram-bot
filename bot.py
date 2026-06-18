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
CANDLE_RESOLUTION = "1"
CANDLE_LOOKBACK_SECONDS = 3600


def get_market_data(symbol):
    try:
        if not API_KEY:
            print("ERROR: FINNHUB_API_KEY not found")
            return None

        quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"
        quote = requests.get(quote_url, timeout=5).json()

        price = float(quote.get("c", 0))
        prev_close = float(quote.get("pc", 0))

        if price == 0 or prev_close == 0:
            print(f"{symbol} QUOTE BAD:", quote)
            return None

        change_pct = ((price - prev_close) / prev_close) * 100

        now = int(time.time())
        start = now - CANDLE_LOOKBACK_SECONDS

        candle_url = (
            f"https://finnhub.io/api/v1/stock/candle"
            f"?symbol={symbol}&resolution={CANDLE_RESOLUTION}"
            f"&from={start}&to={now}&token={API_KEY}"
        )

        candles = requests.get(candle_url, timeout=5).json()

        closes = candles.get("c", [])
        volumes = candles.get("v", [])
        status = candles.get("s", "missing")

        print(
            f"{symbol} DATA CHECK | "
            f"QUOTE OK | "
            f"CANDLE STATUS: {status} | "
            f"CLOSES: {len(closes)} | "
            f"VOLUMES: {len(volumes)}"
        )

        if status != "ok":
            return None

        if not closes or not volumes or len(closes) < 5 or len(volumes) < 5:
            return None

        return {
            "price": price,
            "change_pct": change_pct,
            "closes": closes,
            "volumes": volumes
        }

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None


def build_structure(market_data):
    change_pct = market_data["change_pct"]
    closes = market_data["closes"]
    volumes = market_data["volumes"]

    current_volume = volumes[-1]
    avg_volume = sum(volumes[:-1]) / max(len(volumes[:-1]), 1)

    if avg_volume == 0:
        rvol = 0
    else:
        rvol = current_volume / avg_volume

    recent_change = ((closes[-1] - closes[-4]) / closes[-4]) * 100

    if rvol >= 3.0:
        volume = "EXTREME"
    elif rvol >= 2.5:
        volume = "SURGING"
    elif rvol >= 2.0:
        volume = "EXPANDING"
    elif rvol >= 1.5:
        volume = "ELEVATED"
    else:
        volume = "NORMAL"

    if change_pct >= 10 and recent_change <= 0:
        velocity = "STALLING"
    elif recent_change >= 1.0:
        velocity = "EXTREME"
    elif recent_change >= 0.50:
        velocity = "ACCELERATING"
    elif recent_change >= 0.20:
        velocity = "HIGH"
    elif recent_change <= -0.50:
        velocity = "REVERSING"
    elif recent_change >= 0:
        velocity = "BUILDING"
    else:
        velocity = "MODERATE"

    return volume, velocity, rvol, recent_change


def run():
    print("IAL ENGINE LIVE — LOCKED STRUCTURE DIAGNOSTIC ACTIVE")

    while True:
        for symbol in TICKERS:
            try:
                market_data = get_market_data(symbol)

                if not market_data:
                    print(f"SKIPPING {symbol} — bad data")
                    continue

                price = market_data["price"]
                change_pct = market_data["change_pct"]

                volume, velocity, rvol, recent_change = build_structure(market_data)

                signal = classify_signal(
                    price,
                    change_pct,
                    volume,
                    velocity
                )

                state = signal.get("state", "UNKNOWN")

                if state == "BASELINE":
                    print(
                        f"BASELINE: {symbol} | "
                        f"{round(change_pct, 2)}% | "
                        f"RVOL {round(rvol, 2)} | "
                        f"RECENT {round(recent_change, 2)}% | "
                        f"{volume}/{velocity}"
                    )
                    continue

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
