import os
import time
from datetime import datetime

import requests

from watchlist import TICKERS
from rvol_engine import calculate_rvol
from price_engine import calculate_price_activity
from signal_logic import classify_signal
from send_alert import send_alert
from state_engine import should_alert, get_previous_state


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

# 120 price observations require 121 prior sessions.
MIN_HISTORICAL_SESSIONS = 121
MAX_HISTORICAL_MONTHS = 8

HISTORICAL_BAR_CACHE = {}


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


def parse_intraday_series(series):
    bars = []

    for timestamp in sorted(series.keys()):
        bar = series[timestamp]

        close = float(bar.get("4. close", 0))
        volume = float(bar.get("5. volume", 0))

        if close > 0 and volume > 0:
            bars.append(
                {
                    "timestamp": timestamp,
                    "close": close,
                    "volume": volume,
                }
            )

    return bars


def merge_bars(*bar_groups):
    merged = {}

    for bars in bar_groups:
        for bar in bars:
            merged[bar["timestamp"]] = bar

    return [
        merged[timestamp]
        for timestamp in sorted(merged.keys())
    ]


def get_month_string(timestamp, months_back):
    dt = datetime.strptime(
        timestamp,
        "%Y-%m-%d %H:%M:%S"
    )

    total_months = (
        dt.year * 12
        + (dt.month - 1)
        - months_back
    )

    year = total_months // 12
    month = (total_months % 12) + 1

    return f"{year:04d}-{month:02d}"


def count_prior_sessions(bars, current_date):
    dates = {
        bar["timestamp"].split(" ")[0]
        for bar in bars
        if bar["timestamp"].split(" ")[0] < current_date
    }

    return len(dates)


def get_historical_intraday(
    symbol,
    latest_timestamp,
    current_bars
):
    current_date = latest_timestamp.split(" ")[0]

    cached_bars = HISTORICAL_BAR_CACHE.get(
        symbol,
        []
    )

    cached_bars = merge_bars(
        cached_bars,
        current_bars
    )

    prior_sessions = count_prior_sessions(
        cached_bars,
        current_date
    )

    if prior_sessions < MIN_HISTORICAL_SESSIONS:
        print(
            f"{symbol} HISTORY WARMUP | "
            f"CURRENT SESSIONS: {prior_sessions}"
        )

        for months_back in range(
            1,
            MAX_HISTORICAL_MONTHS + 1
        ):
            month = get_month_string(
                latest_timestamp,
                months_back
            )

            month_url = (
                f"https://www.alphavantage.co/query"
                f"?function=TIME_SERIES_INTRADAY"
                f"&symbol={symbol}"
                f"&interval={INTRADAY_INTERVAL}"
                f"&month={month}"
                f"&outputsize=full"
                f"&extended_hours=false"
                f"&apikey={API_KEY}"
            )

            month_data = get_json(
                month_url,
                f"{symbol} HISTORY {month}"
            )

            if not month_data:
                continue

            if "Note" in month_data:
                print(
                    f"{symbol} ALPHA LIMIT {month}:",
                    month_data["Note"]
                )
                continue

            if "Information" in month_data:
                print(
                    f"{symbol} ALPHA INFO {month}:",
                    month_data["Information"]
                )
                continue

            if "Error Message" in month_data:
                print(
                    f"{symbol} ALPHA ERROR {month}:",
                    month_data["Error Message"]
                )
                continue

            month_series = month_data.get(
                f"Time Series ({INTRADAY_INTERVAL})"
            )

            if not month_series:
                print(
                    f"{symbol} HISTORY BAD | {month}"
                )
                continue

            month_bars = parse_intraday_series(
                month_series
            )

            cached_bars = merge_bars(
                cached_bars,
                month_bars
            )

            prior_sessions = count_prior_sessions(
                cached_bars,
                current_date
            )

            print(
                f"{symbol} HISTORY {month} | "
                f"PRIOR SESSIONS: {prior_sessions}"
            )

            if (
                prior_sessions
                >= MIN_HISTORICAL_SESSIONS
            ):
                break

    HISTORICAL_BAR_CACHE[symbol] = cached_bars

    final_sessions = count_prior_sessions(
        cached_bars,
        current_date
    )

    print(
        f"{symbol} HISTORY READY | "
        f"PRIOR SESSIONS: {final_sessions}"
    )

    return cached_bars


def get_market_data(symbol):
    try:
        if not API_KEY:
            print(
                "ERROR: ALPHA_VANTAGE_API_KEY not found"
            )
            return None

        # ==================================================
        # REAL-TIME QUOTE
        # ==================================================

        quote_url = (
            f"https://www.alphavantage.co/query"
            f"?function=GLOBAL_QUOTE"
            f"&symbol={symbol}"
            f"&entitlement=realtime"
            f"&apikey={API_KEY}"
        )

        quote = get_json(
            quote_url,
            f"{symbol} QUOTE"
        )

        if not quote:
            return None

        if "Note" in quote:
            print(
                f"{symbol} ALPHA LIMIT:",
                quote["Note"]
            )
            return None

        if "Information" in quote:
            print(
                f"{symbol} ALPHA INFO:",
                quote["Information"]
            )
            return None

        if "Error Message" in quote:
            print(
                f"{symbol} ALPHA ERROR:",
                quote["Error Message"]
            )
            return None

        global_quote = quote.get(
            "Global Quote",
            {}
        )

        price = float(
            global_quote.get(
                "05. price",
                0
            )
        )

        previous_close = float(
            global_quote.get(
                "08. previous close",
                0
            )
        )

        if (
            price == 0
            or previous_close == 0
        ):
            print(
                f"{symbol} QUOTE BAD:",
                quote
            )
            return None

        # ==================================================
        # CURRENT INTRADAY HISTORY
        # ==================================================

        candle_url = (
            f"https://www.alphavantage.co/query"
            f"?function=TIME_SERIES_INTRADAY"
            f"&symbol={symbol}"
            f"&interval={INTRADAY_INTERVAL}"
            f"&outputsize=full"
            f"&extended_hours=false"
            f"&entitlement=realtime"
            f"&apikey={API_KEY}"
        )

        candles = get_json(
            candle_url,
            f"{symbol} INTRADAY"
        )

        if not candles:
            return None

        if "Note" in candles:
            print(
                f"{symbol} ALPHA LIMIT:",
                candles["Note"]
            )
            return None

        if "Information" in candles:
            print(
                f"{symbol} ALPHA INFO:",
                candles["Information"]
            )
            return None

        if "Error Message" in candles:
            print(
                f"{symbol} ALPHA ERROR:",
                candles["Error Message"]
            )
            return None

        series = candles.get(
            f"Time Series ({INTRADAY_INTERVAL})"
        )

        if not series:
            print(
                f"{symbol} INTRADAY BAD:",
                candles
            )
            return None

        current_bars = parse_intraday_series(
            series
        )

        print(
            f"{symbol} DATA CHECK | "
            f"CURRENT BARS: {len(current_bars)}"
        )

        if len(current_bars) < 5:
            print(
                f"{symbol} INSUFFICIENT "
                f"INTRADAY DATA: "
                f"{len(current_bars)}"
            )
            return None

        latest_timestamp = (
            current_bars[-1]["timestamp"]
        )

        bars = get_historical_intraday(
            symbol=symbol,
            latest_timestamp=latest_timestamp,
            current_bars=current_bars,
        )

        return {
            "price": price,
            "previous_close": previous_close,
            "bars": bars,
        }

    except Exception as e:
        print(
            f"Error fetching {symbol}: {e}"
        )
        return None


def run():
    print("=" * 60)
    print(
        "IAL ENGINE LIVE â€” "
        "COMPARTMENTALIZED METRICS"
    )
    print("=" * 60)

    while True:
        for symbol in TICKERS:
            try:
                market_data = get_market_data(
                    symbol
                )

                if not market_data:
                    print(
                        f"SKIPPING {symbol} â€” bad data"
                    )
                    continue

                price = market_data["price"]
                previous_close = (
                    market_data["previous_close"]
                )
                bars = market_data["bars"]

                # ==================================================
                # RVOL ENGINE
                # ==================================================

                rvol_data = calculate_rvol(
                    bars
                )

                volume = rvol_data["volume"]
                rvol = rvol_data["rvol"]
                participation_pct = (
                    rvol_data["participation_pct"]
                )

                # ==================================================
                # PRICE ENGINE
                # ==================================================

                price_data = calculate_price_activity(
                    bars=bars,
                    current_price=price,
                    previous_close=previous_close,
                )

                change_pct = (
                    price_data["change_pct"]
                )

                price_activity_ratio = (
                    price_data["price_activity_ratio"]
                )

                recent_change = (
                    price_data["recent_change"]
                )

                velocity = (
                    price_data["velocity"]
                )

                # ==================================================
                # STATE + CLASSIFICATION
                # ==================================================

                previous_state = (
                    get_previous_state(symbol)
                )

                signal = classify_signal(
                    price=price,
                    change_pct=change_pct,
                    volume=volume,
                    velocity=velocity,
                    previous_state=previous_state,
                    rvol=rvol,
                    participation_pct=participation_pct,
                    recent_change=recent_change,
                    price_activity_ratio=price_activity_ratio,
                )

                state = signal.get(
                    "state",
                    "UNKNOWN"
                )

                if state == "BASELINE":
                    print(
                        f"BASELINE: {symbol} | "
                        f"{change_pct:.2f}% | "
                        f"RVOL {rvol:.2f} | "
                        f"PRICE RATIO "
                        f"{price_activity_ratio:.2f}x | "
                        f"RECENT "
                        f"{recent_change:.2f}% | "
                        f"{volume}/{velocity}"
                    )
                    continue

                if should_alert(
                    symbol,
                    state
                ):
                    send_alert(
                        symbol=symbol,
                        price=price,
                        change_pct=change_pct,
                        signal=signal,
                        rvol=rvol,
                        participation_pct=participation_pct,
                    )

                    print(
                        f"ALERT: {symbol} | "
                        f"{signal['name']} | "
                        f"RVOL {rvol:.2f} | "
                        f"PRICE RATIO "
                        f"{price_activity_ratio:.2f}x"
                    )

                else:
                    print(
                        f"NO DUPLICATE: "
                        f"{symbol} - {state}"
                    )

            except Exception as e:
                print(
                    f"Error with {symbol}: {e}"
                )

        time.sleep(
            CHECK_INTERVAL
        )


if __name__ == "__main__":
    run()
