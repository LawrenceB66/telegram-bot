import io
from contextlib import redirect_stdout

from rvol_engine import calculate_rvol
from price_engine import calculate_price_activity
from signal_logic import classify_signal
from state_engine import (
    _signal_family,
    _material_signal_change,
    _material_driver_change,
)


REPEAT_ALERT_MOVE_PCT = 5.0
RECONSTRUCTION_SESSIONS = 5


def _group_sessions(bars):
    sessions = {}

    for bar in bars:
        session_date = bar["timestamp"].split(" ")[0]
        sessions.setdefault(session_date, []).append(bar)

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

    previous_date = session_dates[
        index - 1
    ]

    previous_session = sessions.get(
        previous_date,
        []
    )

    if not previous_session:
        return None

    return float(
        previous_session[-1]["close"]
    )


def _new_event(
    state,
    trading_date,
    price,
    change_pct,
    rvol,
    price_activity_ratio,
    signal_name,
    driver,
    signal_family,
):
    return {
        "state": state,
        "event_start_date": trading_date,
        "event_start_price": price,
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
        "latest_signal_family": signal_family,
        "last_alert_signal_name": signal_name,
        "last_alert_driver": driver,
        "last_alert_signal_family": signal_family,
        "alert_count": 1,
        "continuation_count": 0,
        "last_event_type": (
            "RECONSTRUCTED_NEW_EVENT"
        ),
        "last_move_from_alert_pct": 0,
    }


def _apply_observation(
    event,
    state,
    trading_date,
    price,
    change_pct,
    rvol,
    price_activity_ratio,
    signal_name,
    driver,
    signal_family,
):
    if event is None:
        return _new_event(
            state=state,
            trading_date=trading_date,
            price=price,
            change_pct=change_pct,
            rvol=rvol,
            price_activity_ratio=(
                price_activity_ratio
            ),
            signal_name=signal_name,
            driver=driver,
            signal_family=signal_family,
        )

    last_alert_date = event.get(
        "last_alert_date"
    )

    last_alert_price = event.get(
        "last_alert_price"
    )

    last_alert_family = event.get(
        "last_alert_signal_family"
    )

    if not last_alert_family:
        last_alert_family = _signal_family(
            signal_name=event.get(
                "last_alert_signal_name"
            ),
            state=event.get("state"),
        )

    last_alert_driver = event.get(
        "last_alert_driver"
    )

    move_from_last_alert_pct = 0

    if (
        last_alert_price is not None
        and float(last_alert_price) != 0
    ):
        move_from_last_alert_pct = (
            (
                float(price)
                - float(last_alert_price)
            )
            / float(last_alert_price)
        ) * 100

    material_move = (
        abs(move_from_last_alert_pct)
        >= REPEAT_ALERT_MOVE_PCT
    )

    material_signal_change = (
        _material_signal_change(
            last_family=last_alert_family,
            new_family=signal_family,
        )
    )

    material_driver_change = (
        _material_driver_change(
            last_driver=last_alert_driver,
            new_driver=driver,
        )
    )

    new_session = (
        last_alert_date != trading_date
    )

    event.update(
        {
            "state": state,
            "latest_date": trading_date,
            "latest_price": price,
            "latest_change_pct": change_pct,
            "latest_rvol": rvol,
            "latest_price_activity_ratio": (
                price_activity_ratio
            ),
            "latest_signal_name": signal_name,
            "latest_driver": driver,
            "latest_signal_family": (
                signal_family
            ),
            "last_move_from_alert_pct": (
                move_from_last_alert_pct
            ),
        }
    )

    if not (
        material_signal_change
        or material_driver_change
        or material_move
    ):
        event[
            "last_event_type"
        ] = "RECONSTRUCTED_SUPPRESSED"

        return event

    alert_count = int(
        event.get(
            "alert_count",
            1
        )
    ) + 1

    continuation_count = int(
        event.get(
            "continuation_count",
            0
        )
    )

    if new_session:
        continuation_count += 1

    if material_signal_change:
        if new_session:
            event_type = (
                "RECONSTRUCTED_"
                "CONTINUATION_SIGNAL_CHANGE"
            )
        else:
            event_type = (
                "RECONSTRUCTED_SIGNAL_CHANGE"
            )

    elif material_driver_change:
        if new_session:
            event_type = (
                "RECONSTRUCTED_"
                "CONTINUATION_DRIVER_CHANGE"
            )
        else:
            event_type = (
                "RECONSTRUCTED_DRIVER_CHANGE"
            )

    else:
        if new_session:
            event_type = (
                "RECONSTRUCTED_CONTINUATION"
            )
        else:
            event_type = (
                "RECONSTRUCTED_REPEAT"
            )

    event.update(
        {
            "last_alert_date": trading_date,
            "last_alert_price": price,
            "last_alert_signal_name": (
                signal_name
            ),
            "last_alert_driver": driver,
            "last_alert_signal_family": (
                signal_family
            ),
            "alert_count": alert_count,
            "continuation_count": (
                continuation_count
            ),
            "last_event_type": event_type,
        }
    )

    return event


def reconstruct_event_memory(
    bars,
    exclude_latest=True
):
    """
    Rebuild recent event memory from historical
    market observations.

    Reconstruction uses the same metric and
    classification engines as the live scanner,
    but suppresses their normal diagnostic output.

    When exclude_latest is True, the entire most
    recent trading session is excluded so live
    observations are not reconstructed as history.
    """

    if not bars:
        return None

    ordered_bars = sorted(
        bars,
        key=lambda item: item["timestamp"]
    )

    if exclude_latest:
        latest_date = ordered_bars[
            -1
        ]["timestamp"].split(" ")[0]

        working_bars = [
            bar
            for bar in ordered_bars
            if bar["timestamp"].split(" ")[0]
            < latest_date
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

    if len(session_dates) < 122:
        return None

    target_dates = session_dates[
        -RECONSTRUCTION_SESSIONS:
    ]

    event = None
    previous_state = None

    all_bars = []

    for session_date in session_dates:
        session_bars = sessions[
            session_date
        ]

        if session_date not in target_dates:
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

        for bar in session_bars:
            all_bars.append(
                bar
            )

            try:
                with redirect_stdout(
                    io.StringIO()
                ):
                    rvol_data = calculate_rvol(
                        all_bars
                    )

                    price_data = (
                        calculate_price_activity(
                            bars=all_bars,
                            current_price=bar["close"],
                            previous_close=(
                                previous_close
                            ),
                        )
                    )

            except Exception:
                continue

            signal = classify_signal(
                price=bar["close"],
                change_pct=price_data[
                    "change_pct"
                ],
                volume=rvol_data[
                    "volume"
                ],
                velocity=price_data[
                    "velocity"
                ],
                previous_state=previous_state,
                rvol=rvol_data[
                    "rvol"
                ],
                participation_pct=rvol_data[
                    "participation_pct"
                ],
                recent_change=price_data[
                    "recent_change"
                ],
                price_activity_ratio=price_data[
                    "price_activity_ratio"
                ],
            )

            state = signal.get(
                "state",
                "BASELINE"
            )

            if state == "BASELINE":
                continue

            signal_name = signal.get(
                "name"
            )

            driver = signal.get(
                "driver"
            )

            signal_family = _signal_family(
                signal_name=signal_name,
                state=state,
            )

            event = _apply_observation(
                event=event,
                state=state,
                trading_date=session_date,
                price=float(
                    bar["close"]
                ),
                change_pct=float(
                    price_data[
                        "change_pct"
                    ]
                ),
                rvol=float(
                    rvol_data[
                        "rvol"
                    ]
                ),
                price_activity_ratio=float(
                    price_data[
                        "price_activity_ratio"
                    ]
                ),
                signal_name=signal_name,
                driver=driver,
                signal_family=signal_family,
            )

            previous_state = state

    return event
