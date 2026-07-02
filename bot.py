import time
import requests
import os

from signal_logic import classify_signal
from send_alert import send_alert
from state_engine import should_alert

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

print("API_KEY repr:", repr(API_KEY))
print("API_KEY type:", type(API_KEY))
print("API_KEY len:", len(API_KEY) if API_KEY is not None else "None")

print("=" * 60)
print("IAL STARTUP DIAGNOSTICS")
print("=" * 60)

if API_KEY:
    print("ALPHA VANTAGE KEY FOUND: YES")
    print("KEY LENGTH:", len(API_KEY))
    print(f"KEY PREVIEW: {API_KEY[:2]}...{API_KEY[-2:]}")
else:
    print("ALPHA VANTAGE KEY FOUND: NO")

print("=" * 60)

TICKERS = [
    "AMC", "GME", "CVNA", "UPST",
    "SOFI", "HOOD", "AFRM", "DKNG",
    "MARA", "RIOT", "COIN",
    "AI", "PLTR",
    "LCID", "RIVN", "NIO", "XPEV"
]

CHECK_INTERVAL = 30
INTRADAY_INTERVAL = "5min"


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
            print("ERROR: ALPHA_VANTAGE_API_KEY not found")
            return None

        quote_url = (
            f"https://www.alphavantage.co/query"
            f"?function=GLOBAL_QUOTE"
            f"&symbol={symbol}"
            f"&apikey={API_KEY}"
        )

        quote = get_json(quote_url, f"{symbol} QUOTE")
        if not quote:
            return None

        if "Note" in quote:
            print(f"{symbol} ALPHA LIMIT:", quote["Note"])
            return None

        if "Information" in quote:
            print(f"{symbol} ALPHA INFO:", quote["Information"])
            return None

        if "Error Message" in quote:
            print(f"{symbol} ALPHA ERROR:", quote["Error Message"])
            return None

        global_quote = quote.get("Global Quote", {})

        price = float(global_quote.get("05. price", 0))
        prev_close = float(global_quote.get("08. previous close", 0))

        if price == 0 or prev_close == 0:
            print(f"{symbol} QUOTE BAD:", quote)
            return None

        change_pct = ((price - prev_close) / prev_close) * 100

        candle_url = (
            f"https://www.alphavantage.co/query"
            f"?function=TIME_SERIES_INTRADAY"
            f"&symbol={symbol}"
            f"&interval={INTRADAY_INTERVAL}"
            f"&outputsize=full"
            f"&apikey={API_KEY}"
        )

        candles = get_json(candle_url, f"{symbol} INTRADAY")
        if not candles:
            return None

        if "Note" in candles:
            print(f"{symbol} ALPHA LIMIT:", candles["Note"])
            return None

        if "Information" in candles:
            print(f"{symbol} ALPHA INFO:", candles["Information"])
            return None

        if "Error Message" in candles:
            print(f"{symbol} ALPHA ERROR:", candles["Error Message"])
            return None

        series = candles.get(f"Time Series ({INTRADAY_INTERVAL})")
        if not series:
            print(f"{symbol} INTRADAY BAD:", candles)
            return None

        closes = []
        volumes = []

        for timestamp in sorted(series.keys()):
            bar = series[timestamp]

            close = float(bar.get("4. close", 0))
            volume = float(bar.get("5. volume", 0))

            if close > 0 and volume > 0:
                closes.append(close)
                volumes.append(volume)

        print(
            f"{symbol} DATA CHECK | "
            f"BARS: {len(closes)} | "
            f"VOLUMES: {len(volumes)}"
        )

        if len(closes) < 5:
            print(f"{symbol} INSUFFICIENT INTRADAY DATA:", len(closes))
            return None

        return {
            "price": price,
            "change_pct": change_pct,
            "closes": closes,
            "volumes": volumes,
        }

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def build_structure(market_data):
    change_pct = market_data["change_pct"]
    closes = market_data["closes"]
    volumes = market_data["volumes"]

    current_volume = volumes[-1]
    prior = volumes[:-21:-1]
    avg = sum(prior) / max(len(prior), 1)
    rvol = 0 if avg == 0 else current_volume / avg

    recent_change = (
        0
        if closes[-4] == 0
        else ((closes[-1] - closes[-4]) / closes[-4]) * 100
    )

    volume = (
        "EXTREME" if rvol >= 3 else
        "SURGING" if rvol >= 2.5 else
        "EXPANDING" if rvol >= 2 else
        "ELEVATED" if rvol >= 1.5 else
        "NORMAL"
    )

    if change_pct >= 10 and recent_change <= 0:
        velocity = "STALLING"
    elif recent_change >= 1:
        velocity = "EXTREME"
    elif recent_change >= 0.5:
        velocity = "ACCELERATING"
    elif recent_change >= 0.2:
        velocity = "HIGH"
    elif recent_change <= -0.5:
        velocity = "REVERSING"
    elif recent_change >= 0:
        velocity = "BUILDING"
    else:
        velocity = "MODERATE"

    return volume, velocity, rvol, recent_change


def run():
    print("=" * 60)
    print("IAL ENGINE LIVE — ALPHA VANTAGE TEST")
    print("=" * 60)

    while True:
        for symbol in TICKERS:
            try:
                md = get_market_data(symbol)

                if not md:
                    print(f"SKIPPING {symbol} — bad data")
                    continue

                price = md["price"]
                change_pct = md["change_pct"]

                volume, velocity, rvol, recent_change = build_structure(md)

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
                    send_alert(
                        symbol,
                        price,
                        change_pct,
                        signal
                    )
                    print(f"SENT CLEAN: {symbol} - {state}")
                else:
                    print(f"NO DUPLICATE: {symbol} - {state}")

            except Exception as e:
                print(f"Error with {symbol}: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run()
