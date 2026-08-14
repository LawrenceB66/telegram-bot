from rvol_engine import calculate_rvol
from price_engine import calculate_price_activity
from signal_logic import classify_signal


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


def _previous_close(session_dates, sessions, session_date):
    try:
        index = session_dates.index(session_date)
    except ValueError:
        return None

    if index <= 0:
        return None

    previous_date = session_dates[index - 1]
    previous_session = sessions.get(previous_date, [])

    if not previous_session:
        return None

    return float(previous_session[-1]["close"])


def _new_event(
    state,
    trading_date,
    price,
    change_pct,
    rvol,
    price_activity_ratio
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
        "latest_price_activity_ratio": price_activity_ratio,
        "alert_count": 1,
        "continuation_count": 0,
        "last_event_type": "RECONSTRUCTED_NEW_EVENT",
        "last_move_from_alert_pct": 0,
    }


def _apply_observation(
    event,
    state,
    trading_date,
    price,
    change_pct,
    rvol,
    price_activity_ratio
):
    if event is None:
        return _new_event(
            state=state,
            trading_date=trading_date,
            price=price,
            change_pct=change_pct,
            rvol=rvol,
            price_activity_ratio=price_activity_ratio,
        )

    last_state = event.get("state")
    last_alert_date = event.get("last_alert_date")
    last_alert_price = event.get("last_alert_price")

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

    event["latest_date"] = trading_date
    event["latest_price"] = price
    event["latest_change_pct"] = change_pct
    event["latest_rvol"] = rvol
    event["latest_price_activity_ratio"] = (
        price_activity_ratio
    )
    event["last_move_from_alert_pct"] = (
        move_from_last_alert_pct
    )

    state_changed = (
        last_state != state
    )

    material_move = (
        abs(move_from_last_alert_pct)
        >= REPEAT_ALERT_MOVE_PCT
    )

    if not state_changed and not material_move:
        event["state"] = state
        event["last_event_type"] = (
            "RECONSTRUCTED_SUPPRESSED"
        )
        return event

    alert_count = int(
        event.get("alert_count", 1)
    ) + 1

    continuation_count = int(
        event.get("continuation_count", 0)
    )

    new_session = (
        last_alert_date != trading_date
    )

    if new_session:
        continuation_count += 1

    event.update(
        {
            "state": state,
            "last_alert_date": trading_date,
            "last_alert_price": price,
            "alert_count": alert_count,
            "continuation_count": continuation_count,
            "last_event_type": (
                "RECONSTRUCTED_CONTINUATION"
                if new_session
                else "RECONSTRUCTED_REPEAT"
            ),
        }
    )

    return event


def reconstruct_event_memory(
    bars,
    exclude_latest=True
):
    """
    Rebuild recent event memory from market history.

    This is intentionally derived from the same historical
    bars already used by the live metric engines. It does
    not depend on Railway storage or any external database.

    The reconstruction scans only the most recent sessions
    needed to recover the current event chain.
    """

    if not bars:
        return None

    working_bars = (
        bars[:-1]
        if exclude_latest and len(bars) > 1
        else list(bars)
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
            session_date
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
            all_bars.append(bar)

            rvol_data = calculate_rvol(
                all_bars
            )

            price_data = (
                calculate_price_activity(
                    bars=all_bars,
                    current_price=bar["close"],
                    previous_close=previous_close,
                )
            )

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

            event = _apply_observation(
                event=event,
                state=state,
                trading_date=session_date,
                price=float(bar["close"]),
                change_pct=float(
                    price_data["change_pct"]
                ),
                rvol=float(
                    rvol_data["rvol"]
                ),
                price_activity_ratio=float(
                    price_data[
                        "price_activity_ratio"
                    ]
                ),
            )

            previous_state = state

    return event