import os
import time
from datetime import datetime

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
# IAL COMPOSITE RVOL STANDARD
#
# Four cumulative same-time historical baselines:
#
# 20 sessions
# 60 sessions
# 90 sessions
# 120 sessions
#
# The four baseline averages are themselves averaged
# into one composite volume baseline.
# ==================================================

RVOL_LOOKBACKS = (20, 60, 90, 120)
MAX_RVOL_LOOKBACK = 120

# Alpha Vantage's normal full intraday response
# supplies the most recent 30 days. Historical month
# slices are loaded only as needed and cached.
MAX_HISTORICAL_MONTHS = 8

HISTORICAL_BAR_CACHE = {}


def get_json(url, label):
    try:
        response = requests.get(
            url,
            timeout=10
        )

        if response.status_code != 200:
            print(
                f"{label} HTTP ERROR:",
                response.status_code,
                response.text[:200]
            )
            return None

        return response.json()

    except Exception as e:
        print(
            f"{label} REQUEST ERROR:",
            e
        )
        return None


def parse_intraday_series(series):
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


def count_prior_sessions(
    bars,
    current_date
):
    dates = {
        bar["timestamp"].split(" ")[0]
        for bar in bars
        if (
            bar["timestamp"].split(" ")[0]
            < current_date
        )
    }

    return len(dates)


def get_historical_intraday(
    symbol,
    latest_timestamp,
    current_bars
):
    current_date = (
        latest_timestamp.split(" ")[0]
    )

    cached_bars = HISTORICAL_BAR_CACHE.get(
        symbol,
        []
    )

    # Keep adding the latest rolling intraday bars
    # to the cache as the engine runs.
    cached_bars = merge_bars(
        cached_bars,
        current_bars
    )

    prior_sessions = count_prior_sessions(
        cached_bars,
        current_date
    )

    # ==================================================
    # HISTORICAL WARMUP
    #
    # Pull earlier calendar months only until we have
    # at least 120 unique prior trading sessions.
    #
    # Alpha Vantage supports historical intraday
    # month slices through month=YYYY-MM.
    # ==================================================

    if prior_sessions < MAX_RVOL_LOOKBACK:

        print(
            f"{symbol} RVOL HISTORY WARMUP | "
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
                    f"{symbol} ALPHA LIMIT "
                    f"{month}:",
                    month_data["Note"]
                )
                continue

            if "Information" in month_data:
                print(
                    f"{symbol} ALPHA INFO "
                    f"{month}:",
                    month_data["Information"]
                )
                continue

            if "Error Message" in month_data:
                print(
                    f"{symbol} ALPHA ERROR "
                    f"{month}:",
                    month_data["Error Message"]
                )
                continue

            month_series = month_data.get(
                f"Time Series "
                f"({INTRADAY_INTERVAL})"
            )

            if not month_series:
                print(
                    f"{symbol} HISTORY BAD | "
                    f"{month}"
                )
                continue

            month_bars = parse_intraday_series(
                month_series
            )

            cached_bars = merge_bars(
                cached_bars,
                month_bars
            )

            prior_sessions = (
                count_prior_sessions(
                    cached_bars,
                    current_date
                )
            )

            print(
                f"{symbol} HISTORY {month} | "
                f"PRIOR SESSIONS: "
                f"{prior_sessions}"
            )

            if (
                prior_sessions
                >= MAX_RVOL_LOOKBACK
            ):
                break

    HISTORICAL_BAR_CACHE[symbol] = (
        cached_bars
    )

    final_sessions = count_prior_sessions(
        cached_bars,
        current_date
    )

    print(
        f"{symbol} RVOL HISTORY READY | "
        f"PRIOR SESSIONS: "
        f"{final_sessions}"
    )

    return cached_bars


def get_market_data(symbol):
    try:
        if not API_KEY:
            print(
                "ERROR: "
                "ALPHA_VANTAGE_API_KEY not found"
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

        prev_close = float(
            global_quote.get(
                "08. previous close",
                0
            )
        )

        if (
            price == 0
            or prev_close == 0
        ):
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
        # CURRENT INTRADAY HISTORY
        #
        # Regular session only:
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
            f"Time Series "
            f"({INTRADAY_INTERVAL})"
        )

        if not series:
            print(
                f"{symbol} INTRADAY BAD:",
                candles
            )
            return None

        current_bars = (
            parse_intraday_series(series)
        )

        print(
            f"{symbol} DATA CHECK | "
            f"CURRENT BARS: "
            f"{len(current_bars)}"
        )

        if len(current_bars) < 5:
            print(
                f"{symbol} "
                f"INSUFFICIENT INTRADAY DATA:",
                len(current_bars)
            )
            return None

        latest_timestamp = (
            current_bars[-1]["timestamp"]
        )

        # ==================================================
        # LOAD / REUSE HISTORICAL INTRADAY CACHE
        # ==================================================

        bars = get_historical_intraday(
            symbol=symbol,
            latest_timestamp=latest_timestamp,
            current_bars=current_bars,
        )

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

    current_timestamp = (
        current_bar["timestamp"]
    )

    current_date = (
        current_timestamp.split(" ")[0]
    )

    current_time = (
        current_timestamp
        .split(" ")[1][:5]
    )

    # ==================================================
    # GROUP BARS BY TRADING SESSION
    # ==================================================

    sessions = {}

    for bar in bars:

        timestamp = bar["timestamp"]

        bar_date = (
            timestamp.split(" ")[0]
        )

        bar_time = (
            timestamp.split(" ")[1][:5]
        )

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
    # ==================================================

    current_cumulative_volume = 0

    for bar in sessions.get(
        current_date,
        []
    ):
        if bar["time"] <= current_time:
            current_cumulative_volume += (
                bar["volume"]
            )

    # ==================================================
    # PRIOR SESSION DATES
    # ==================================================

    historical_session_dates = sorted(
        [
            session_date
            for session_date
            in sessions.keys()
            if session_date < current_date
        ],
        reverse=True
    )

    # ==================================================
    # BUILD CUMULATIVE SAME-TIME VOLUME
    # FOR EACH PRIOR SESSION
    # ==================================================

    historical_cumulative_volumes = []

    for session_date in (
        historical_session_dates
    ):

        cumulative_volume = 0

        for bar in sessions[session_date]:

            if bar["time"] <= current_time:
                cumulative_volume += (
                    bar["volume"]
                )

        if cumulative_volume > 0:
            historical_cumulative_volumes.append(
                cumulative_volume
            )

    # ==================================================
    # FAIL CLOSED
    #
    # A true 20/60/90/120 composite requires
    # all 120 prior sessions.
    # ==================================================

    if (
        len(historical_cumulative_volumes)
        < MAX_RVOL_LOOKBACK
    ):

        avg_20 = 0
        avg_60 = 0
        avg_90 = 0
        avg_120 = 0

        composite_average = 0

        rvol = 0
        participation_pct = 0

    else:

        # Most recent N prior sessions.
        avg_20 = (
            sum(
                historical_cumulative_volumes[
                    :20
                ]
            )
            / 20
        )

        avg_60 = (
            sum(
                historical_cumulative_volumes[
                    :60
                ]
            )
            / 60
        )

        avg_90 = (
            sum(
                historical_cumulative_volumes[
                    :90
                ]
            )
            / 90
        )

        avg_120 = (
            sum(
                historical_cumulative_volumes[
                    :120
                ]
            )
            / 120
        )

        # ==================================================
        # IAL COMPOSITE BASELINE
        #
        # Equal weighting:
        #
        # 20D  = 25%
        # 60D  = 25%
        # 90D  = 25%
        # 120D = 25%
        # ==================================================

        composite_average = (
            avg_20
            + avg_60
            + avg_90
            + avg_120
        ) / 4

        rvol = (
            0
            if composite_average == 0
            else (
                current_cumulative_volume
                / composite_average
            )
        )

        participation_pct = (
            (rvol - 1) * 100
            if rvol > 0
            else 0
        )

    # ==================================================
    # COMPOSITE RVOL VALIDATION LOG
    # ==================================================

    print(
        f"COMPOSITE RVOL | "
        f"TIME {current_time} | "
        f"CURRENT "
        f"{int(current_cumulative_volume)} | "
        f"20D {int(avg_20)} | "
        f"60D {int(avg_60)} | "
        f"90D {int(avg_90)} | "
        f"120D {int(avg_120)} | "
        f"COMPOSITE "
        f"{int(composite_average)} | "
        f"RVOL {rvol:.2f} | "
        f"PART "
        f"{participation_pct:+.0f}%"
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
    #
    # These thresholds now operate on the
    # COMPOSITE RVOL metric.
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
    print(
        "IAL ENGINE LIVE — "
        "COMPOSITE RVOL"
    )
    print("=" * 60)

    while True:

        for symbol in TICKERS:

            try:
                md = get_market_data(
                    symbol
                )

                if not md:
                    print(
                        f"SKIPPING {symbol} — "
                        f"bad data"
                    )
                    continue

                price = md["price"]
                change_pct = (
                    md["change_pct"]
                )

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
                        f"RVOL "
                        f"{round(rvol, 2)} | "
                        f"RECENT "
                        f"{round(recent_change, 2)}% | "
                        f"{volume}/"
                        f"{velocity}"
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
                        f"COMPOSITE RVOL "
                        f"{rvol:.2f}"
                    )

                else:
                    print(
                        f"NO DUPLICATE: "
                        f"{symbol} - {state}"
                    )

            except Exception as e:
                print(
                    f"Error with "
                    f"{symbol}: {e}"
                )

        time.sleep(
            CHECK_INTERVAL
        )


if __name__ == "__main__":
    run()
