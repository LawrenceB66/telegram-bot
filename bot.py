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
CANDLE_LOOKBACK_SECONDS = 259200  # 3 days
CANDLE_DELAY_SECONDS = 300        # avoid incomplete newest candle


def get_json(url, label):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"{label} HTTP ERROR:", response.status_code, response.text[:200])
            return None
        return response.json()
    except Exception as e:
        print(f"{label} REQUEST ERROR:", e)
        return None


def get_market_data(symbol):
    try:
        if not API_KEY:
            print("ERROR: FINNHUB_API_KEY not found")
            return None

        quote_url = f"https://na01.safelinks.protection.outlook.com/?url=https%3A%2F%2Ffinnhub.io%2Fapi%2Fv1%2Fquote%3Fsymbol%3D&data=05%7C02%7C%7C8dd5e897d568468a876308ded2d30f9a%7C84df9e7fe9f640afb435aaaaaaaaaaaa%7C1%7C0%7C639180001102574257%7CUnknown%7CTWFpbGZsb3d8eyJFbXB0eU1hcGkiOnRydWUsIlYiOiIwLjAuMDAwMCIsIlAiOiJXaW4zMiIsIkFOIjoiTWFpbCIsIldUIjoyfQ%3D%3D%7C0%7C%7C%7C&sdata=QyZqezL3hMXbWZyqQ%2BlRJDv%2FC%2B38iLhY%2BA%2FEVjCvXOk%3D&reserved=0{symbol}&token={API_KEY}"
        quote = get_json(quote_url, f"{symbol} QUOTE")

        if not quote:
            return None

        price = float(quote.get("c", 0))
        prev_close = float(quote.get("pc", 0))

        if price == 0 or prev_close == 0:
            print(f"{symbol} QUOTE BAD:", quote)
            return None

        change_pct = ((price - prev_close) / prev_close) * 100

        now = int(time.time()) - CANDLE_DELAY_SECONDS
        start = now - CANDLE_LOOKBACK_SECONDS

        candle_url = (
            f"https://na01.safelinks.protection.outlook.com/?url=https%3A%2F%2Ffinnhub.io%2Fapi%2Fv1%2Fstock%2Fcandle&data=05%7C02%7C%7C8dd5e897d568468a876308ded2d30f9a%7C84df9e7fe9f640afb435aaaaaaaaaaaa%7C1%7C0%7C639180001102608204%7CUnknown%7CTWFpbGZsb3d8eyJFbXB0eU1hcGkiOnRydWUsIlYiOiIwLjAuMDAwMCIsIlAiOiJXaW4zMiIsIkFOIjoiTWFpbCIsIldUIjoyfQ%3D%3D%7C0%7C%7C%7C&sdata=oQYEOCSeHg%2FtNzrRH97xxOvOKWqPzGW8ONHIWs97CGk%3D&reserved=0"
            f"?symbol={symbol}"
            f"&resolution={CANDLE_RESOLUTION}"
            f"&from={start}"
            f"&to={now}"
            f"&token={API_KEY}"
        )

        candles = get_json(candle_url, f"{symbol} CANDLES")

        if not candles:
            return None

        status = candles.get("s", "missing")
        closes = candles.get("c", [])
        volumes = candles.get("v", [])
        timestamps = candles.get("t", [])

        print(
            f"{symbol} DATA CHECK | "
            f"QUOTE OK | "
            f"CANDLE STATUS: {status} | "
            f"CLOSES: {len(closes)} | "
            f"VOLUMES: {len(volumes)} | "
            f"TIMES: {len(timestamps)}"
        )

        if status != "ok":
            print(f"{symbol} CANDLE BAD:", candles)
            return None

        cleaned = [
            (c, v)
            for c, v in zip(closes, volumes)
            if c is not None and v is not None and float(c) > 0 and float(v) > 0
        ]

        if len(cleaned) < 5:
            print(f"{symbol} CANDLE INSUFFICIENT AFTER CLEANING:", len(cleaned))
            return None

        closes = [float(item[0]) for item in cleaned]
        volumes = [float(item[1]) for item in cleaned]

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
    prior_volumes = volumes[:-1]

    avg_volume = sum(prior_volumes) / max(len(prior_volumes), 1)

    if avg_volume == 0:
        rvol = 0
    else:
        rvol = current_volume / avg_volume

    if closes[-4] == 0:
        recent_change = 0
    else:
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
    print("IAL ENGINE LIVE — CANDLE PIPELINE RESTORE v1.0")

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
