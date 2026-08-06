import os
import time

import requests

from watchlist import TICKERS
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

CHECK_INTERVAL = 30
INTRADAY_INTERVAL = "5min"


def get_json(url, label):
    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            print(
                f"{label} HTTP ERROR:",
                response.status_code,
                response.text[:200]
            )
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
            f"&entitlement=realtime"
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
            f"&entitlement=realtime"
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
            print(
                f"{symbol} INSUFFICIENT INTRADAY DATA:",
                len(closes)
            )
            return None

        return {
            "price": price,
            "change_pct": change_pct,
            "closes": closes,

def run():

    while True:

        print("=" * 60)
        print("NEW SCAN")
        print("=" * 60)

        for symbol in TICKERS:

            market_data = get_market_data(symbol)

            if not market_data:
                print(f"SKIPPING {symbol} - bad data")
                continue

            structure = build_structure(market_data)

            signal = classify_signal(

                price=market_data["price"],

                change_pct=market_data["change_pct"],

                volume=structure["volume_label"],

                velocity=structure["velocity_label"],

                rvol=structure["rvol"],

                participation_pct=structure["participation_pct"],

                recent_change=structure["recent_change"]

            )

            if signal["state"] == "BASELINE":

                print(
                    f"BASELINE: {symbol} | "
                    f"{market_data['change_pct']:.2f}% | "
                    f"RVOL {structure['rvol']:.2f}"
                )

                continue

            if not should_alert(symbol, signal["state"]):

                print(f"SUPPRESSED: {symbol}")

                continue

            send_alert(

                symbol=symbol,

                price=market_data["price"],

                change_pct=market_data["change_pct"],

                signal=signal,

                rvol=structure["rvol"],

                participation_pct=structure["participation_pct"]

            )

            print(
                f"ALERT: {symbol} | "
                f"{signal['name']} | "
                f"RVOL {structure['rvol']:.2f}"
            )

        print(
            f"Sleeping {CHECK_INTERVAL} seconds..."
        )

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run()
