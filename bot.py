import os
import time

import requests

from watchlist import TICKERS
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

# ==================================================
# IAL INTRADAY RVOL STANDARD
#
# Current cumulative regular-session volume
# divided by average cumulative volume through
# the same time across the prior 20 sessions.
# ==================================================

RVOL_LOOKBACK_SESSIONS = 20
MIN_COMPARABLE_SESSIONS = 20


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

        prev_close = float(
            global_quote.get(
                "08. previous close",
                0
            )
        )

        if price == 0 or prev_close == 0:
            print(
                f"{symbol} QUOTE BAD:",
                quote
            )
            return None

        change_pct = (
            (price - prev_close)
            / prev_close
        ) * 100

        # ==================================================
        # INTRADAY HISTORY
        #
        # Regular trading session only.
        # 9:30 AM - 4:00 PM Eastern.
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

        # ==================================================
        # BUILD ORDERED BAR HISTORY
        # ==================================================

        bars = []

        for timestamp in sorted(series.keys()):
            bar = series[timestamp]

            close = float(
                bar.get(
                    "4. close",
                    0
                )
            )

            volume = float(
                bar.get(
                    "5. volume",
                    0
                )
            )

            if close > 0 and volume > 0:
                bars.append(
                    {
                        "timestamp": timestamp,
                        "close": close,
                        "volume": volume,
                    }
                )

        print(
            f"{symbol} DATA CHECK | "
            f"BARS: {len(bars)} | "
            f"VOLUMES: {len(bars)}"
        )

        if len(bars) < 5:
            print(
                f"{symbol} INSUFFICIENT INTRADAY DATA:",
                len(bars)
            )
            return None

        return {
            "price": price,
            "change_pct": change_pct,
            "bars": bars,
        }

    except Exception as e:
        print(
            f"Error fetching {symbol}: {e}"
        )
        return None


def build_structure(market_data):

    change_pct = market_data["change_pct"]
    bars = market_data["bars"]

    # ==================================================
    # CURRENT SESSION / CURRENT TIME
    # ==================================================

    current_bar = bars[-1]

    current_timestamp = current_bar["timestamp"]

    current_date = current_timestamp.split(" ")[0]
    current_time = current_timestamp.split(" ")[1][:5]

    # ==================================================
    # GROUP BARS BY TRADING SESSION
    # ==================================================

    sessions = {}

    for bar in bars:

        timestamp = bar["timestamp"]

        bar_date = timestamp.split(" ")[0]
        bar_time = timestamp.split(" ")[1][:5]

        if bar_date not in sessions:
            sessions[bar_date] = []

        sessions[bar_date].append(
            {
                "time": bar_time,
                "volume": bar["volume"],
            }
        )

    # ==================================================
    # CURRENT CUMULATIVE SESSION VOLUME
    #
    # Sum today's regular-session volume from the open
    # through the latest available 5-minute time slot.
    # ==================================================

    current_cumulative_volume = 0

    for bar in sessions.get(current_date, []):

        if bar["time"] <= current_time:
            current_cumulative_volume += bar["volume"]

    # ==================================================
    # HISTORICAL CUMULATIVE SAME-TIME BASELINE
    #
    # For each prior trading session:
    #
    # Sum volume from the regular-session open
    # through the same clock time as today.
    #
    # Then average those cumulative totals across
    # the prior 20 trading sessions.
    # ==================================================

    historical_session_dates = sorted(
        [
            session_date
            for session_date in sessions.keys()
            if session_date < current_date
        ],
        reverse=True
    )

    historical_cumulative_volumes = []

    for session_date in historical_session_dates:

        cumulative_volume = 0

        for bar in sessions[session_date]:

            if bar["time"] <= current_time:
                cumulative_volume += bar["volume"]

        if cumulative_volume > 0:

            historical_cumulative_volumes.append(
                cumulative_volume
            )

        if (
            len(historical_cumulative_volumes)
            >= RVOL_LOOKBACK_SESSIONS
        ):
            break

    # ==================================================
    # FAIL CLOSED IF 20 PRIOR SESSIONS ARE UNAVAILABLE
    # ==================================================

    comparable_sessions = len(
        historical_cumulative_volumes
    )

    if (
        comparable_sessions
        < MIN_COMPARABLE_SESSIONS
    ):

        average_cumulative_volume = 0
        rvol = 0
        participation_pct = 0

    else:

        average_cumulative_volume = (
            sum(historical_cumulative_volumes)
            / comparable_sessions
        )

        rvol = (
            0
            if average_cumulative_volume == 0
            else (
                current_cumulative_volume
                / average_cumulative_volume
            )
        )

        participation_pct = (
            (rvol - 1) * 100
            if rvol > 0
            else 0
        )

    # ==================================================
    # RVOL VALIDATION LOG
    # ==================================================

    print(
        f"RVOL CHECK | "
        f"TIME {current_time} | "
        f"CURRENT CUM {int(current_cumulative_volume)} | "
        f"AVG{comparable_sessions} "
        f"{int(average_cumulative_volume)} | "
        f"RVOL {rvol:.2f} | "
        f"PART {participation_pct:+.0f}%"
    )

    # ==================================================
    # RECENT PRICE MOVEMENT
    # ==================================================

    closes = [
        bar["close"]
        for bar in bars
    ]

    recent_change = (
        0
        if closes[-4] == 0
        else (
            (
                closes[-1]
                - closes[-4]
            )
            / closes[-4]
        ) * 100
    )

    # ==================================================
    # VOLUME CLASSIFICATION
    # ==================================================

    volume = (
        "EXTREME" if rvol >= 3 else
        "SURGING" if rvol >= 2.5 else
        "EXPANDING" if rvol >= 2 else
        "ELEVATED" if rvol >= 1.5 else
        "NORMAL"
    )

    # ==================================================
    # VELOCITY CLASSIFICATION
    # ==================================================

    if (
        change_pct >= 10
        and recent_change <= 0
    ):
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

    return (
        volume,
        velocity,
        rvol,
        participation_pct,
        recent_change,
    )


def run():

    print("=" * 60)
    print("IAL ENGINE LIVE — ALPHA VANTAGE TEST")
    print("=" * 60)

    while True:

        for symbol in TICKERS:

            try:
                md = get_market_data(
                    symbol
                )

                if not md:
                    print(
                        f"SKIPPING {symbol} — bad data"
                    )
                    continue

                price = md["price"]
                change_pct = md["change_pct"]

                (
                    volume,
                    velocity,
                    rvol,
                    participation_pct,
                    recent_change,
                ) = build_structure(md)

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
                )

                state = signal.get(
                    "state",
                    "UNKNOWN"
                )

                if state == "BASELINE":
                    print(
                        f"BASELINE: {symbol} | "
                        f"{round(change_pct, 2)}% | "
                        f"RVOL {round(rvol, 2)} | "
                        f"RECENT "
                        f"{round(recent_change, 2)}% | "
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
                        f"RVOL {rvol:.2f}"
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
