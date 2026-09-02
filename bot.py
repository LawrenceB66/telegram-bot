import os
import time
from datetime import datetime

import requests

from watchlist import TICKERS
from rvol_engine import calculate_rvol
from price_engine import calculate_price_activity
from signal_logic import classify_signal
from event_memory import reconstruct_event_memory
from send_alert import send_alert
from state_engine import (
    should_alert,
    get_previous_state,
    get_previous_event,
    get_alert_context,
    seed_event,
)


API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

print("=" * 60)
print("IAL STARTUP DIAGNOSTICS")
print("=" * 60)

if API_KEY:
    print("ALPHA VANTAGE KEY FOUND: YES")
    print("KEY LENGTH:", len(API_KEY))
else:
    print("ALPHA VANTAGE KEY FOUND: NO")

print("=" * 60)


CHECK_INTERVAL = 30
INTRADAY_INTERVAL = "5min"

MIN_HISTORICAL_SESSIONS = 201
MAX_HISTORICAL_MONTHS = 13

HISTORICAL_BAR_CACHE = {}

EVENT_MEMORY_RECONSTRUCTED = set()


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

        high = float(
            bar.get(
                "2. high",
                0
            )
        )

        low = float(
            bar.get(
                "3. low",
                0
            )
        )

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

        if (
            high > 0
            and low > 0
            and close > 0
            and volume > 0
        ):
            bars.append(
                {
                    "timestamp": timestamp,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                }
            )

    return bars


def merge_bars(*bar_groups):
    merged = {}

    for bars in bar_groups:
        for bar in bars:
            merged[
                bar["timestamp"]
            ] = bar

    return [
        merged[timestamp]
        for timestamp in sorted(
            merged.keys()
        )
    ]


def get_month_string(
    timestamp,
    months_back
):
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
    month = (
        total_months % 12
    ) + 1

    return (
        f"{year:04d}-"
        f"{month:02d}"
    )


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

    return len(
        dates
    )


def get_historical_intraday(
    symbol,
    latest_timestamp,
    current_bars
):
    current_date = (
        latest_timestamp.split(" ")[0]
    )

    cached_bars = (
        HISTORICAL_BAR_CACHE.get(
            symbol,
            []
        )
    )

    cached_bars = merge_bars(
        cached_bars,
        current_bars
    )

    prior_sessions = (
        count_prior_sessions(
            cached_bars,
            current_date
        )
    )

    if (
        prior_sessions
        < MIN_HISTORICAL_SESSIONS
    ):
        print(
            f"{symbol} HISTORY WARMUP | "
            f"CURRENT SESSIONS: "
            f"{prior_sessions}"
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
                    month_data[
                        "Information"
                    ]
                )
                continue

            if "Error Message" in month_data:
                print(
                    f"{symbol} ALPHA ERROR {month}:",
                    month_data[
                        "Error Message"
                    ]
                )
                continue

            month_series = (
                month_data.get(
                    f"Time Series "
                    f"({INTRADAY_INTERVAL})"
                )
            )

            if not month_series:
                print(
                    f"{symbol} HISTORY BAD | "
                    f"{month}"
                )
                continue

            month_bars = (
                parse_intraday_series(
                    month_series
                )
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
                >= MIN_HISTORICAL_SESSIONS
            ):
                break

    HISTORICAL_BAR_CACHE[
        symbol
    ] = cached_bars

    final_sessions = (
        count_prior_sessions(
            cached_bars,
            current_date
        )
    )

    print(
        f"{symbol} HISTORY READY | "
        f"PRIOR SESSIONS: "
        f"{final_sessions}"
    )

    return cached_bars


def get_market_data(symbol):
    try:
        if not API_KEY:
            print(
                "ERROR: "
                "ALPHA_VANTAGE_API_KEY "
                "not found"
            )
            return None

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
                quote[
                    "Error Message"
                ]
            )
            return None

        global_quote = (
            quote.get(
                "Global Quote",
                {}
            )
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
                candles[
                    "Information"
                ]
            )
            return None

        if "Error Message" in candles:
            print(
                f"{symbol} ALPHA ERROR:",
                candles[
                    "Error Message"
                ]
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
            parse_intraday_series(
                series
            )
        )

        print(
            f"{symbol} DATA CHECK | "
            f"CURRENT BARS: "
            f"{len(current_bars)}"
        )

        if (
            len(current_bars) < 5
        ):
            print(
                f"{symbol} INSUFFICIENT "
                f"INTRADAY DATA: "
                f"{len(current_bars)}"
            )
            return None

        latest_timestamp = (
            current_bars[-1][
                "timestamp"
            ]
        )

        bars = get_historical_intraday(
            symbol=symbol,
            latest_timestamp=(
                latest_timestamp
            ),
            current_bars=current_bars,
        )

        return {
            "price": price,
            "previous_close": (
                previous_close
            ),
            "latest_timestamp": (
                latest_timestamp
            ),
            "bars": bars,
        }

    except Exception as e:
        print(
            f"Error fetching "
            f"{symbol}: {e}"
        )
        return None


def ensure_event_memory(
    symbol,
    bars
):
    if (
        symbol
        in EVENT_MEMORY_RECONSTRUCTED
    ):
        return

    EVENT_MEMORY_RECONSTRUCTED.add(
        symbol
    )

    if (
        get_previous_event(symbol)
        is not None
    ):
        return

    try:
        reconstructed_event = (
            reconstruct_event_memory(
                bars=bars,
                exclude_latest=True,
            )
        )

        if reconstructed_event:
            seed_event(
                symbol,
                reconstructed_event
            )

            print(
                f"EVENT MEMORY RESTORED: "
                f"{symbol} | "
                f"STATE "
                f"{reconstructed_event.get('state')} | "
                f"COUNT "
                f"{reconstructed_event.get('alert_count', 1)} | "
                f"LAST ALERT "
                f"{reconstructed_event.get('last_alert_price')}"
            )

        else:
            print(
                f"EVENT MEMORY EMPTY: "
                f"{symbol}"
            )

    except Exception as e:
        print(
            f"EVENT MEMORY ERROR: "
            f"{symbol} | {e}"
        )


def run():
    print("=" * 60)
    print(
        "IAL ENGINE LIVE — "
        "COMPARTMENTALIZED METRICS"
    )
    print("=" * 60)

    while True:
        for symbol in TICKERS:
            try:
                market_data = (
                    get_market_data(
                        symbol
                    )
                )

                if not market_data:
                    print(
                        f"SKIPPING "
                        f"{symbol} — bad data"
                    )
                    continue

                price = (
                    market_data[
                        "price"
                    ]
                )

                previous_close = (
                    market_data[
                        "previous_close"
                    ]
                )

                latest_timestamp = (
                    market_data[
                        "latest_timestamp"
                    ]
                )

                trading_date = (
                    latest_timestamp.split(
                        " "
                    )[0]
                )

                bars = (
                    market_data[
                        "bars"
                    ]
                )

                # ==================================================
                # EVENT MEMORY
                # ==================================================

                ensure_event_memory(
                    symbol=symbol,
                    bars=bars,
                )

                # ==================================================
                # RVOL ENGINE
                # ==================================================

                rvol_data = calculate_rvol(
                    bars
                )

                volume = (
                    rvol_data[
                        "volume"
                    ]
                )

                rvol = (
                    rvol_data[
                        "rvol"
                    ]
                )

                participation_pct = (
                    rvol_data[
                        "participation_pct"
                    ]
                )

                # ==================================================
                # PRICE ENGINE
                # ==================================================

                price_data = (
                    calculate_price_activity(
                        bars=bars,
                        current_price=price,
                        previous_close=(
                            previous_close
                        ),
                    )
                )

                change_pct = (
                    price_data[
                        "change_pct"
                    ]
                )

                price_activity_ratio = (
                    price_data[
                        "price_activity_ratio"
                    ]
                )

                recent_change = (
                    price_data[
                        "recent_change"
                    ]
                )

                velocity = (
                    price_data[
                        "velocity"
                    ]
                )

                drawdown_from_high_pct = (
                    price_data[
                        "drawdown_from_high_pct"
                    ]
                )

                rebound_from_low_pct = (
                    price_data[
                        "rebound_from_low_pct"
                    ]
                )

                # ==================================================
                # STATE + CLASSIFICATION
                # ==================================================

                previous_state = (
                    get_previous_state(
                        symbol
                    )
                )

                signal = classify_signal(
                    price=price,
                    change_pct=change_pct,
                    volume=volume,
                    velocity=velocity,
                    previous_state=(
                        previous_state
                    ),
                    rvol=rvol,
                    participation_pct=(
                        participation_pct
                    ),
                    recent_change=(
                        recent_change
                    ),
                    price_activity_ratio=(
                        price_activity_ratio
                    ),
                    drawdown_from_high_pct=(
                        drawdown_from_high_pct
                    ),
                    rebound_from_low_pct=(
                        rebound_from_low_pct
                    ),
                )

                state = signal.get(
                    "state",
                    "UNKNOWN"
                )

                # ==================================================
                # STATE ENGINE
                # ==================================================

                alert_allowed = (
                    should_alert(
                        symbol=symbol,
                        new_state=state,
                        trading_date=(
                            trading_date
                        ),
                        observation_timestamp=(
                            latest_timestamp
                        ),
                        price=price,
                        change_pct=(
                            change_pct
                        ),
                        rvol=rvol,
                        price_activity_ratio=(
                            price_activity_ratio
                        ),
                        signal_name=(
                            signal.get(
                                "name"
                            )
                        ),
                        driver=(
                            signal.get(
                                "driver"
                            )
                        ),
                    )
                )

                # ==================================================
                # BASELINE
                # ==================================================

                if (
                    state
                    == "BASELINE"
                ):
                    alert_context = (
                        get_alert_context(
                            symbol
                        )
                    )

                    print(
                        f"BASELINE: "
                        f"{symbol} | "
                        f"{change_pct:.2f}% | "
                        f"RVOL "
                        f"{rvol:.2f} | "
                        f"PRICE RATIO "
                        f"{price_activity_ratio:.2f}x | "
                        f"RECENT "
                        f"{recent_change:.2f}% | "
                        f"FROM HIGH "
                        f"{drawdown_from_high_pct:+.2f}% | "
                        f"FROM LOW "
                        f"{rebound_from_low_pct:+.2f}% | "
                        f"{volume}/{velocity}"
                    )

                    continue

                # ==================================================
                # ALERT
                # ==================================================

                if alert_allowed:
                    alert_context = (
                        get_alert_context(
                            symbol
                        )
                    )

                    signal[
                        "event_type"
                    ] = alert_context.get(
                        "event_type"
                    )

                    signal[
                        "alert_count"
                    ] = alert_context.get(
                        "alert_count",
                        1
                    )

                    signal[
                        "alert_label"
                    ] = alert_context.get(
                        "alert_label"
                    )

                    signal[
                        "continuation_count"
                    ] = alert_context.get(
                        "continuation_count",
                        0
                    )

                    send_alert(
                        symbol=symbol,
                        price=price,
                        change_pct=(
                            change_pct
                        ),
                        signal=signal,
                        rvol=rvol,
                        participation_pct=(
                            participation_pct
                        ),
                    )

                    print(
                        f"ALERT: "
                        f"{symbol} | "
                        f"{signal['name']} | "
                        f"EVENT "
                        f"{alert_context.get('event_type')} | "
                        f"COUNT "
                        f"{alert_context.get('alert_count', 1)} | "
                        f"LABEL "
                        f"{alert_context.get('alert_label') or '1st Alert'} | "
                        f"DRIVER "
                        f"{signal.get('driver') or 'N/A'} | "
                        f"RVOL "
                        f"{rvol:.2f} | "
                        f"PRICE RATIO "
                        f"{price_activity_ratio:.2f}x | "
                        f"FROM HIGH "
                        f"{drawdown_from_high_pct:+.2f}% | "
                        f"FROM LOW "
                        f"{rebound_from_low_pct:+.2f}%"
                    )

                else:
                    alert_context = (
                        get_alert_context(
                            symbol
                        )
                    )

                    print(
                        f"SUPPRESSED: "
                        f"{symbol} - "
                        f"{state} | "
                        f"DRIVER "
                        f"{signal.get('driver') or 'N/A'} | "
                        f"MOVE FROM LAST ALERT "
                        f"{alert_context.get('last_move_from_alert_pct', 0):+.2f}% | "
                        f"FROM HIGH "
                        f"{drawdown_from_high_pct:+.2f}% | "
                        f"FROM LOW "
                        f"{rebound_from_low_pct:+.2f}%"
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
