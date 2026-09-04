import io
from contextlib import redirect_stdout

from rvol_engine import (
    calculate_rvol,
    MAX_RVOL_LOOKBACK,
)
from price_engine import (
    calculate_price_activity,
    MAX_PRICE_LOOKBACK,
)
from signal_logic import classify_signal


RECONSTRUCTION_SESSIONS = 5

MIN_RECONSTRUCTION_SESSIONS = (
    max(
        MAX_RVOL_LOOKBACK,
        MAX_PRICE_LOOKBACK,
    )
    + RECONSTRUCTION_SESSIONS
    + 1
)


def _group_sessions(bars):
    sessions = {}

    for bar in bars:
        session_date = (
            bar["timestamp"].split(" ")[0]
        )

        sessions.setdefault(
            session_date,
            []
        ).append(
            bar
        )

    for session_date in sessions:
        sessions[session_date].sort(
            key=lambda item: item["timestamp"]
        )

    return sessions


def _previous_close(
    session_dates,
    sessions,
    session_date
):
    try:
        index = session_dates.index(
            session_date
        )

    except ValueError:
        return None

    if index <= 0:
        return None

    previous_date = (
        session_dates[index - 1]
    )

    previous_session = sessions.get(
        previous_date,
        []
    )

    if not previous_session:
        return None

    return float(
        previous_session[-1]["close"]
    )


def _historical_context(
    state,
    trading_date,
    timestamp,
    price,
    change_pct,
    rvol,
    price_activity_ratio,
    signal_name,
    driver,
    drawdown_from_high_pct,
    rebound_from_low_pct,
):
    """
    Historical reconstruction is context only.

    It must never become live-session state and must
    never carry historical alert numbering into the
    current trading session.
    """

    return {
        # ==================================================
        # LIVE STATE IS INTENTIONALLY EMPTY
        # ==================================================

        "state": None,

        # ==================================================
        # HISTORICAL CONTEXT
        # ==================================================

        "historical_state": state,
        "historical_date": trading_date,
        "historical_timestamp": timestamp,
        "historical_price": price,
        "historical_change_pct": change_pct,
        "historical_rvol": rvol,
        "historical_price_activity_ratio": (
            price_activity_ratio
        ),
        "historical_signal_name": signal_name,
        "historical_driver": driver,
        "historical_drawdown_from_high_pct": (
            drawdown_from_high_pct
        ),
        "historical_rebound_from_low_pct": (
            rebound_from_low_pct
        ),

        # ==================================================
        # STATE ENGINE COMPATIBILITY
        #
        # Dates remain historical so state_engine.py can
        # recognize and close the prior-session context
        # before creating the current live event.
        # ==================================================

        "event_start_date": None,
        "event_start_price": None,

        "last_alert_date": trading_date,
        "last_alert_price": price,

        "latest_date": trading_date,
        "latest_price": price,
        "latest_change_pct": change_pct,
        "latest_rvol": rvol,
        "latest_price_activity_ratio": (
            price_activity_ratio
        ),

        "latest_signal_name": signal_name,
        "latest_driver": driver,
        "latest_signal_family": None,

        "last_alert_signal_name": signal_name,
        "last_alert_driver": driver,
        "last_alert_signal_family": None,

        # ==================================================
        # ALERT NUMBERING NEVER RECONSTRUCTED
        # ==================================================

        "alert_count": 0,
        "continuation_count": 0,

        "baseline_count": 0,
        "last_baseline_timestamp": None,

        "last_event_type": (
            "HISTORICAL_CONTEXT"
        ),

        "last_move_from_alert_pct": 0,
    }


def reconstruct_event_memory(
    bars,
    exclude_latest=True
):
    """
    Reconstruct recent historical market context.

    Historical reconstruction uses the same RVOL,
    Price Engine, and Signal Logic calculations as
    the live scanner.

    Reconstruction is deliberately separated from
    live-session state:

    • historical alert counts are never restored
    • previous_state resets at every session boundary
    • the latest historical classification is stored
      as context only
    • live state remains None

    When exclude_latest is True, the complete latest
    trading session is excluded from reconstruction.
    """

    if not bars:
        return None

    ordered_bars = sorted(
        bars,
        key=lambda item: item["timestamp"]
    )

    if exclude_latest:
        latest_date = (
            ordered_bars[-1][
                "timestamp"
            ].split(" ")[0]
        )

        working_bars = [
            bar
            for bar in ordered_bars
            if (
                bar["timestamp"].split(" ")[0]
                < latest_date
            )
        ]

    else:
        working_bars = list(
            ordered_bars
        )

    if not working_bars:
        return None

    sessions = _group_sessions(
        working_bars
    )

    session_dates = sorted(
        sessions.keys()
    )

    # ==================================================
    # 200D RECONSTRUCTION REQUIREMENT
    #
    # Earliest reconstructed session requires:
    #
    # 200 prior same-time observations
    # + preceding session close
    # + reconstruction window
    # ==================================================

    if (
        len(session_dates)
        < MIN_RECONSTRUCTION_SESSIONS
    ):
        return None

    target_dates = (
        session_dates[
            -RECONSTRUCTION_SESSIONS:
        ]
    )

    historical_context = None

    all_bars = []

    for session_date in session_dates:
        session_bars = sessions[
            session_date
        ]

        if (
            session_date
            not in target_dates
        ):
            all_bars.extend(
                session_bars
            )
            continue

        previous_close = _previous_close(
            session_dates,
            sessions,
            session_date,
        )

        if (
            previous_close is None
            or previous_close == 0
        ):
            all_bars.extend(
                session_bars
            )
            continue

        # ==================================================
        # SESSION-SCOPED CLASSIFICATION MEMORY
        #
        # Historical state never crosses a session
        # boundary.
        # ==================================================

        previous_state = None

        for bar in session_bars:
            all_bars.append(
                bar
            )

            try:
                with redirect_stdout(
                    io.StringIO()
                ):
                    rvol_data = (
                        calculate_rvol(
                            all_bars
                        )
                    )

                    price_data = (
                        calculate_price_activity(
                            bars=all_bars,
                            current_price=float(
                                bar["close"]
                            ),
                            previous_close=(
                                previous_close
                            ),
                        )
                    )

            except Exception:
                continue

            change_pct = float(
                price_data[
                    "change_pct"
                ]
            )

            rvol = float(
                rvol_data[
                    "rvol"
                ]
            )

            price_activity_ratio = float(
                price_data[
                    "price_activity_ratio"
                ]
            )

            recent_change = float(
                price_data[
                    "recent_change"
                ]
            )

            drawdown_from_high_pct = float(
                price_data[
                    "drawdown_from_high_pct"
                ]
            )

            rebound_from_low_pct = float(
                price_data[
                    "rebound_from_low_pct"
                ]
            )

            signal = classify_signal(
                price=float(
                    bar["close"]
                ),
                change_pct=change_pct,
                volume=rvol_data[
                    "volume"
                ],
                velocity=price_data[
                    "velocity"
                ],
                previous_state=(
                    previous_state
                ),
                rvol=rvol,
                participation_pct=float(
                    rvol_data[
                        "participation_pct"
                    ]
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
                "BASELINE"
            )

            # ==================================================
            # BASELINE DOES NOT ERASE HISTORICAL
            # SESSION CONTEXT
            # ==================================================

            if state == "BASELINE":
                continue

            signal_name = signal.get(
                "name"
            )

            driver = signal.get(
                "driver"
            )

            # ==================================================
            # PRESERVE STATE ONLY INSIDE THIS
            # HISTORICAL SESSION
            # ==================================================

            previous_state = state

            # ==================================================
            # STORE LATEST QUALIFYING HISTORICAL
            # OBSERVATION
            #
            # No historical alert count is inferred.
            # ==================================================

            historical_context = (
                _historical_context(
                    state=state,
                    trading_date=(
                        session_date
                    ),
                    timestamp=bar[
                        "timestamp"
                    ],
                    price=float(
                        bar["close"]
                    ),
                    change_pct=(
                        change_pct
                    ),
                    rvol=rvol,
                    price_activity_ratio=(
                        price_activity_ratio
                    ),
                    signal_name=(
                        signal_name
                    ),
                    driver=driver,
                    drawdown_from_high_pct=(
                        drawdown_from_high_pct
                    ),
                    rebound_from_low_pct=(
                        rebound_from_low_pct
                    ),
                )
            )

    return historical_context
