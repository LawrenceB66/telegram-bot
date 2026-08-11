RVOL_LOOKBACKS = (20, 60, 90, 120)
MAX_RVOL_LOOKBACK = 120


def calculate_rvol(bars):
    """
    Calculate IAL Composite RVOL using cumulative same-time volume
    across 20, 60, 90, and 120 prior trading sessions.
    """

    if not bars:
        return {
            "volume": "NORMAL",
            "rvol": 0,
            "participation_pct": 0,
            "current_time": "N/A",
            "current_cumulative_volume": 0,
            "avg_20": 0,
            "avg_60": 0,
            "avg_90": 0,
            "avg_120": 0,
            "composite_average": 0,
            "comparable_sessions": 0,
        }

    current_bar = bars[-1]
    current_timestamp = current_bar["timestamp"]

    current_date = current_timestamp.split(" ")[0]
    current_time = current_timestamp.split(" ")[1][:5]

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

    current_cumulative_volume = 0

    for bar in sessions.get(current_date, []):
        if bar["time"] <= current_time:
            current_cumulative_volume += bar["volume"]

    historical_session_dates = sorted(
        [
            session_date
            for session_date in sessions.keys()
            if session_date < current_date
        ],
        reverse=True,
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

    comparable_sessions = len(
        historical_cumulative_volumes
    )

    if comparable_sessions < MAX_RVOL_LOOKBACK:
        avg_20 = 0
        avg_60 = 0
        avg_90 = 0
        avg_120 = 0
        composite_average = 0
        rvol = 0
        participation_pct = 0

    else:
        avg_20 = (
            sum(historical_cumulative_volumes[:20])
            / 20
        )

        avg_60 = (
            sum(historical_cumulative_volumes[:60])
            / 60
        )

        avg_90 = (
            sum(historical_cumulative_volumes[:90])
            / 90
        )

        avg_120 = (
            sum(historical_cumulative_volumes[:120])
            / 120
        )

        composite_average = (
            avg_20
            + avg_60
            + avg_90
            + avg_120
        ) / 4

        rvol = (
            0
            if composite_average == 0
            else current_cumulative_volume / composite_average
        )

        participation_pct = (
            (rvol - 1) * 100
            if rvol > 0
            else 0
        )

    volume = (
        "EXTREME" if rvol >= 3 else
        "SURGING" if rvol >= 2.5 else
        "EXPANDING" if rvol >= 2 else
        "ELEVATED" if rvol >= 1.5 else
        "NORMAL"
    )

    print(
        f"COMPOSITE RVOL | "
        f"TIME {current_time} | "
        f"CURRENT {int(current_cumulative_volume)} | "
        f"20D {int(avg_20)} | "
        f"60D {int(avg_60)} | "
        f"90D {int(avg_90)} | "
        f"120D {int(avg_120)} | "
        f"COMPOSITE {int(composite_average)} | "
        f"RVOL {rvol:.2f} | "
        f"PART {participation_pct:+.0f}%"
    )

    return {
        "volume": volume,
        "rvol": rvol,
        "participation_pct": participation_pct,
        "current_time": current_time,
        "current_cumulative_volume": current_cumulative_volume,
        "avg_20": avg_20,
        "avg_60": avg_60,
        "avg_90": avg_90,
        "avg_120": avg_120,
        "composite_average": composite_average,
        "comparable_sessions": comparable_sessions,
    }
