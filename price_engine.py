PRICE_LOOKBACKS = (20, 60, 120, 200)
MAX_PRICE_LOOKBACK = 200


def calculate_price_activity(
    bars,
    current_price,
    previous_close
):
    """
    Calculate IAL Composite Price Activity.

    Directional change_pct uses the real-time quote.

    Normalized price activity uses the latest completed
    5-minute bar and compares it with historical price
    activity at the same clock time across 20, 60, 120,
    and 200 prior trading sessions.

    Intraday path tracks current-session price location
    relative to the developing session high and low.
    """

    if (
        not bars
        or current_price is None
        or previous_close is None
        or float(previous_close) == 0
    ):
        return _empty_result()

    current_price = float(current_price)
    previous_close = float(previous_close)

    current_bar = bars[-1]
    current_timestamp = current_bar["timestamp"]
    current_bar_close = float(current_bar["close"])

    current_date = current_timestamp.split(" ")[0]
    current_time = current_timestamp.split(" ")[1][:5]

    # ==================================================
    # REAL-TIME DIRECTIONAL PRICE CHANGE
    # ==================================================

    change_pct = (
        (current_price - previous_close)
        / previous_close
    ) * 100

    # ==================================================
    # SAME-TIME PRICE ACTIVITY
    # ==================================================

    current_price_activity = abs(
        (
            current_bar_close
            - previous_close
        )
        / previous_close
        * 100
    )

    # ==================================================
    # GROUP BARS BY TRADING SESSION
    # ==================================================

    sessions = {}

    for bar in bars:
        timestamp = bar["timestamp"]

        bar_date = timestamp.split(" ")[0]
        bar_time = timestamp.split(" ")[1][:5]

        bar_close = float(
            bar["close"]
        )

        bar_high = float(
            bar.get(
                "high",
                bar_close
            )
        )

        bar_low = float(
            bar.get(
                "low",
                bar_close
            )
        )

        if bar_date not in sessions:
            sessions[bar_date] = []

        sessions[bar_date].append(
            {
                "time": bar_time,
                "close": bar_close,
                "high": bar_high,
                "low": bar_low,
            }
        )

    for session_date in sessions:
        sessions[session_date].sort(
            key=lambda item: item["time"]
        )

    session_dates = sorted(
        sessions.keys()
    )

    # ==================================================
    # HISTORICAL SAME-TIME PRICE ACTIVITY
    # ==================================================

    historical_price_activity = []

    prior_dates = [
        session_date
        for session_date in session_dates
        if session_date < current_date
    ]

    for index in range(
        len(prior_dates) - 1,
        0,
        -1
    ):
        session_date = prior_dates[index]

        previous_session_date = (
            prior_dates[index - 1]
        )

        same_time_price = _price_at_or_before(
            sessions[session_date],
            current_time
        )

        previous_session_bars = (
            sessions[previous_session_date]
        )

        prior_session_close = (
            previous_session_bars[-1]["close"]
            if previous_session_bars
            else 0
        )

        if (
            same_time_price is None
            or prior_session_close == 0
        ):
            continue

        activity_pct = abs(
            (
                same_time_price
                - prior_session_close
            )
            / prior_session_close
            * 100
        )

        historical_price_activity.append(
            activity_pct
        )

        if (
            len(historical_price_activity)
            >= MAX_PRICE_LOOKBACK
        ):
            break

    comparable_sessions = len(
        historical_price_activity
    )

    # ==================================================
    # FAIL CLOSED
    # ==================================================

    if (
        comparable_sessions
        < MAX_PRICE_LOOKBACK
    ):
        avg_20 = 0
        avg_60 = 0
        avg_120 = 0
        avg_200 = 0

        composite_price_baseline = 0

        price_activity_ratio = 0
        price_activity_pct = 0

    else:
        avg_20 = (
            sum(
                historical_price_activity[:20]
            )
            / 20
        )

        avg_60 = (
            sum(
                historical_price_activity[:60]
            )
            / 60
        )

        avg_120 = (
            sum(
                historical_price_activity[:120]
            )
            / 120
        )

        avg_200 = (
            sum(
                historical_price_activity[:200]
            )
            / 200
        )

        # ==================================================
        # IAL COMPOSITE PRICE BASELINE
        #
        # Equal weighting:
        #
        # 20D  = 25%
        # 60D  = 25%
        # 120D = 25%
        # 200D = 25%
        # ==================================================

        composite_price_baseline = (
            avg_20
            + avg_60
            + avg_120
            + avg_200
        ) / 4

        price_activity_ratio = (
            0
            if composite_price_baseline == 0
            else (
                current_price_activity
                / composite_price_baseline
            )
        )

        price_activity_pct = (
            (price_activity_ratio - 1) * 100
            if price_activity_ratio > 0
            else 0
        )

    # ==================================================
    # CURRENT SESSION BARS
    # ==================================================

    current_session_bars = [
        item
        for item in sessions.get(
            current_date,
            []
        )
        if item["time"] <= current_time
    ]

    current_session_closes = [
        item["close"]
        for item in current_session_bars
    ]

    # ==================================================
    # INTRADAY PRICE PATH
    # ==================================================

    if current_session_bars:
        completed_session_high = max(
            item["high"]
            for item in current_session_bars
        )

        completed_session_low = min(
            item["low"]
            for item in current_session_bars
        )

        session_high = max(
            completed_session_high,
            current_price
        )

        session_low = min(
            completed_session_low,
            current_price
        )

    else:
        session_high = current_price
        session_low = current_price

    drawdown_from_high_pct = (
        0
        if session_high == 0
        else (
            (
                current_price
                - session_high
            )
            / session_high
        ) * 100
    )

    rebound_from_low_pct = (
        0
        if session_low == 0
        else (
            (
                current_price
                - session_low
            )
            / session_low
        ) * 100
    )

    # ==================================================
    # RECENT PRICE MOVEMENT
    # ==================================================

    if len(current_session_closes) >= 4:
        reference_close = (
            current_session_closes[-4]
        )

        recent_change = (
            0
            if reference_close == 0
            else (
                (
                    current_session_closes[-1]
                    - reference_close
                )
                / reference_close
            ) * 100
        )

    else:
        recent_change = 0

    # ==================================================
    # VELOCITY CLASSIFICATION
    # ==================================================

    if recent_change <= -1.00:
        velocity = "NEGATIVE"

    elif recent_change <= -0.50:
        velocity = "REVERSING"

    elif recent_change <= -0.20:
        velocity = "SLOWING"

    elif (
        change_pct >= 10
        and recent_change <= 0
    ):
        velocity = "STALLING"

    elif recent_change >= 1.00:
        velocity = "EXTREME"

    elif recent_change >= 0.50:
        velocity = "ACCELERATING"

    elif recent_change >= 0.20:
        velocity = "HIGH"

    elif recent_change >= 0:
        velocity = "BUILDING"

    else:
        velocity = "MODERATE"

    # ==================================================
    # PRICE DIAGNOSTIC
    # ==================================================

    print(
        f"COMPOSITE PRICE | "
        f"TIME {current_time} | "
        f"LIVE CHANGE {change_pct:+.2f}% | "
        f"BAR ACTIVITY {current_price_activity:.2f}% | "
        f"20D {avg_20:.2f}% | "
        f"60D {avg_60:.2f}% | "
        f"120D {avg_120:.2f}% | "
        f"200D {avg_200:.2f}% | "
        f"COMPOSITE "
        f"{composite_price_baseline:.2f}% | "
        f"RATIO {price_activity_ratio:.2f}x | "
        f"RECENT {recent_change:+.2f}% | "
        f"SESSION HIGH {session_high:.2f} | "
        f"SESSION LOW {session_low:.2f} | "
        f"FROM HIGH "
        f"{drawdown_from_high_pct:+.2f}% | "
        f"FROM LOW "
        f"{rebound_from_low_pct:+.2f}% | "
        f"VELOCITY {velocity}"
    )

    return {
        "change_pct": change_pct,
        "price_activity": (
            current_price_activity
        ),
        "price_activity_ratio": (
            price_activity_ratio
        ),
        "price_activity_pct": (
            price_activity_pct
        ),
        "recent_change": recent_change,
        "velocity": velocity,
        "current_time": current_time,
        "session_high": session_high,
        "session_low": session_low,
        "drawdown_from_high_pct": (
            drawdown_from_high_pct
        ),
        "rebound_from_low_pct": (
            rebound_from_low_pct
        ),
        "avg_20": avg_20,
        "avg_60": avg_60,
        "avg_120": avg_120,
        "avg_200": avg_200,
        "composite_price_baseline": (
            composite_price_baseline
        ),
        "comparable_sessions": (
            comparable_sessions
        ),
    }


def _price_at_or_before(
    session_bars,
    target_time
):
    selected_price = None

    for bar in session_bars:
        if bar["time"] <= target_time:
            selected_price = bar["close"]
        else:
            break

    return selected_price


def _empty_result():
    return {
        "change_pct": 0,
        "price_activity": 0,
        "price_activity_ratio": 0,
        "price_activity_pct": 0,
        "recent_change": 0,
        "velocity": "MODERATE",
        "current_time": "N/A",
        "session_high": 0,
        "session_low": 0,
        "drawdown_from_high_pct": 0,
        "rebound_from_low_pct": 0,
        "avg_20": 0,
        "avg_60": 0,
        "avg_120": 0,
        "avg_200": 0,
        "composite_price_baseline": 0,
        "comparable_sessions": 0,
    }
