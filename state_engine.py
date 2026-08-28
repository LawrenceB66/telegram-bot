import json
import os
from datetime import date


STATE_FILE = "state.json"

REPEAT_ALERT_MOVE_PCT = 5.0


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)

        return data if isinstance(data, dict) else {}

    except Exception as e:
        print(f"State load error: {e}")
        return {}


def save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)

    except Exception as e:
        print(f"State save error: {e}")


def _normalize_event(raw_event):
    if raw_event is None:
        return None

    if isinstance(raw_event, str):
        return {
            "state": raw_event,
            "event_start_date": None,
            "event_start_price": None,
            "last_alert_date": None,
            "last_alert_price": None,
            "latest_date": None,
            "latest_price": None,
            "latest_change_pct": None,
            "latest_rvol": None,
            "latest_price_activity_ratio": None,
            "latest_signal_name": None,
            "latest_driver": None,
            "latest_signal_family": None,
            "last_alert_signal_name": None,
            "last_alert_driver": None,
            "last_alert_signal_family": None,
            "alert_count": 0,
            "continuation_count": 0,
            "baseline_count": 0,
            "last_baseline_timestamp": None,
            "last_event_type": "LEGACY",
            "last_move_from_alert_pct": 0,
        }

    if isinstance(raw_event, dict):
        return raw_event

    return None


def _safe_float(value):
    try:
        if value is None:
            return None

        return float(value)

    except (TypeError, ValueError):
        return None


def _move_from_last_alert(
    current_price,
    last_alert_price
):
    current_price = _safe_float(
        current_price
    )

    last_alert_price = _safe_float(
        last_alert_price
    )

    if (
        current_price is None
        or last_alert_price is None
        or last_alert_price == 0
    ):
        return 0

    return (
        (
            current_price
            - last_alert_price
        )
        / last_alert_price
    ) * 100


def _ordinal(number):
    number = int(number)

    if 10 <= number % 100 <= 20:
        suffix = "th"

    else:
        suffix = {
            1: "st",
            2: "nd",
            3: "rd",
        }.get(
            number % 10,
            "th"
        )

    return f"{number}{suffix}"


def _normalize_signal_name(signal_name):
    if not signal_name:
        return None

    return str(
        signal_name
    ).strip().upper()


def _normalize_driver(driver):
    if not driver:
        return None

    driver = str(
        driver
    ).strip().upper()

    if driver in {
        "PRICE",
        "VOLUME",
        "PRICE + VOLUME",
    }:
        return driver

    return None


def _signal_family(
    signal_name=None,
    state=None
):
    name = _normalize_signal_name(
        signal_name
    )

    if name:
        if "MOMENTUM SURGE" in name:
            return "MOMENTUM"

        if "ACTIVE EXPANSION" in name:
            return "EXPANSION"

        if "PRESSURE" in name:
            return "PRESSURE"

        if "EXHAUSTION" in name:
            return "EXHAUSTION"

        if "BREAKDOWN" in name:
            return "BREAKDOWN"

    state_name = (
        str(state).strip().upper()
        if state is not None
        else ""
    )

    if state_name in {
        "BUILDING",
        "LOADED",
    }:
        return "EXPANSION"

    if state_name == "EXTENDED":
        return "MOMENTUM"

    if state_name == "EXHAUSTION":
        return "EXHAUSTION"

    if state_name in {
        "FAILURE",
        "DOWNSIDE",
        "BREAKDOWN",
    }:
        return "BREAKDOWN"

    return state_name or None


def _material_signal_change(
    last_family,
    new_family
):
    if (
        not last_family
        or not new_family
        or last_family == new_family
    ):
        return False

    if new_family == "BREAKDOWN":
        return True

    if (
        last_family == "BREAKDOWN"
        and new_family != "BREAKDOWN"
    ):
        return True

    if new_family == "EXHAUSTION":
        return True

    if (
        last_family == "PRESSURE"
        and new_family in {
            "EXPANSION",
            "MOMENTUM",
        }
    ):
        return True

    if (
        new_family == "MOMENTUM"
        and last_family in {
            "PRESSURE",
            "EXPANSION",
        }
    ):
        return True

    return False


def _material_driver_change(
    last_driver,
    new_driver
):
    """
    A driver transition bypasses the ±5% gate only
    when a meaningful new component enters the event.
    """

    last_driver = _normalize_driver(
        last_driver
    )

    new_driver = _normalize_driver(
        new_driver
    )

    if (
        not last_driver
        or not new_driver
        or last_driver == new_driver
    ):
        return False

    material_transitions = {
        (
            "VOLUME",
            "PRICE",
        ),
        (
            "VOLUME",
            "PRICE + VOLUME",
        ),
        (
            "PRICE",
            "PRICE + VOLUME",
        ),
    }

    return (
        last_driver,
        new_driver,
    ) in material_transitions


def _event_session_date(event):
    if not event:
        return None

    return (
        event.get("latest_date")
        or event.get("last_alert_date")
        or event.get("event_start_date")
    )


def seed_event(symbol, event):
    if not event:
        return False

    state = load_state()
    state[symbol] = event
    save_state(state)

    return True


def get_previous_state(symbol):
    state = load_state()

    event = _normalize_event(
        state.get(symbol)
    )

    if not event:
        return None

    return event.get(
        "state"
    )


def get_previous_event(symbol):
    state = load_state()

    return _normalize_event(
        state.get(symbol)
    )


def get_alert_context(symbol):
    event = get_previous_event(
        symbol
    )

    if not event:
        return {
            "event_type": None,
            "alert_count": 0,
            "alert_label": None,
            "continuation_count": 0,
            "event_start_date": None,
            "event_start_price": None,
            "last_alert_date": None,
            "last_alert_price": None,
            "last_move_from_alert_pct": 0,
            "signal_name": None,
            "driver": None,
            "signal_family": None,
            "baseline_count": 0,
            "last_baseline_timestamp": None,
        }

    alert_count = int(
        event.get(
            "alert_count",
            0
        )
    )

    return {
        "event_type": event.get(
            "last_event_type"
        ),
        "alert_count": alert_count,
        "alert_label": (
            None
            if alert_count <= 1
            else f"{_ordinal(alert_count)} Alert"
        ),
        "continuation_count": int(
            event.get(
                "continuation_count",
                0
            )
        ),
        "event_start_date": event.get(
            "event_start_date"
        ),
        "event_start_price": event.get(
            "event_start_price"
        ),
        "last_alert_date": event.get(
            "last_alert_date"
        ),
        "last_alert_price": event.get(
            "last_alert_price"
        ),
        "last_move_from_alert_pct": event.get(
            "last_move_from_alert_pct",
            0
        ),
        "signal_name": event.get(
            "last_alert_signal_name"
        ),
        "driver": event.get(
            "last_alert_driver"
        ),
        "signal_family": event.get(
            "last_alert_signal_family"
        ),
        "baseline_count": 0,
        "last_baseline_timestamp": None,
    }


def should_alert(
    symbol,
    new_state,
    trading_date=None,
    observation_timestamp=None,
    price=None,
    change_pct=None,
    rvol=None,
    price_activity_ratio=None,
    signal_name=None,
    driver=None,
):
    state = load_state()

    previous_event = _normalize_event(
        state.get(symbol)
    )

    current_date = (
        str(trading_date)
        if trading_date is not None
        else date.today().isoformat()
    )

    current_timestamp = (
        str(observation_timestamp)
        if observation_timestamp is not None
        else current_date
    )

    current_price = _safe_float(
        price
    )

    current_change_pct = _safe_float(
        change_pct
    )

    current_rvol = _safe_float(
        rvol
    )

    current_price_activity_ratio = (
        _safe_float(
            price_activity_ratio
        )
    )

    current_signal_name = (
        _normalize_signal_name(
            signal_name
        )
    )

    current_driver = (
        _normalize_driver(
            driver
        )
    )

    current_family = _signal_family(
        signal_name=current_signal_name,
        state=new_state,
    )

    # ==================================================
    # SESSION BOUNDARY
    # ==================================================

    if previous_event is not None:
        previous_session_date = (
            _event_session_date(
                previous_event
            )
        )

        if (
            previous_session_date is not None
            and previous_session_date
            != current_date
        ):
            del state[symbol]
            save_state(state)

            print(
                f"SESSION CLOSED: {symbol} | "
                f"{previous_session_date} → "
                f"{current_date}"
            )

            previous_event = None

    # ==================================================
    # BASELINE
    # ==================================================

    if new_state == "BASELINE":
        if previous_event is None:
            return False

        previous_event.update(
            {
                "latest_date": current_date,
                "latest_price": current_price,
                "latest_change_pct": (
                    current_change_pct
                ),
                "latest_rvol": current_rvol,
                "latest_price_activity_ratio": (
                    current_price_activity_ratio
                ),
                "baseline_count": 0,
                "last_baseline_timestamp": (
                    current_timestamp
                ),
                "last_event_type": "BASELINE",
            }
        )

        state[symbol] = previous_event
        save_state(state)

        return False

    # ==================================================
    # NEW SESSION EVENT
    # ==================================================

    if previous_event is None:
        state[symbol] = {
            "state": new_state,
            "event_start_date": current_date,
            "event_start_price": current_price,
            "last_alert_date": current_date,
            "last_alert_price": current_price,
            "latest_date": current_date,
            "latest_price": current_price,
            "latest_change_pct": current_change_pct,
            "latest_rvol": current_rvol,
            "latest_price_activity_ratio": (
                current_price_activity_ratio
            ),
            "latest_signal_name": (
                current_signal_name
            ),
            "latest_driver": (
                current_driver
            ),
            "latest_signal_family": (
                current_family
            ),
            "last_alert_signal_name": (
                current_signal_name
            ),
            "last_alert_driver": (
                current_driver
            ),
            "last_alert_signal_family": (
                current_family
            ),
            "alert_count": 1,
            "continuation_count": 0,
            "baseline_count": 0,
            "last_baseline_timestamp": None,
            "last_event_type": "NEW_EVENT",
            "last_move_from_alert_pct": 0,
        }

        save_state(state)

        return True

    last_alert_date = previous_event.get(
        "last_alert_date"
    )

    last_alert_price = previous_event.get(
        "last_alert_price"
    )

    # ==================================================
    # LEGACY / MIGRATION
    # ==================================================

    if (
        last_alert_date is None
        or last_alert_price is None
    ):
        previous_event.update(
            {
                "state": new_state,
                "event_start_date": current_date,
                "event_start_price": current_price,
                "last_alert_date": current_date,
                "last_alert_price": current_price,
                "latest_date": current_date,
                "latest_price": current_price,
                "latest_change_pct": (
                    current_change_pct
                ),
                "latest_rvol": current_rvol,
                "latest_price_activity_ratio": (
                    current_price_activity_ratio
                ),
                "latest_signal_name": (
                    current_signal_name
                ),
                "latest_driver": (
                    current_driver
                ),
                "latest_signal_family": (
                    current_family
                ),
                "last_alert_signal_name": (
                    current_signal_name
                ),
                "last_alert_driver": (
                    current_driver
                ),
                "last_alert_signal_family": (
                    current_family
                ),
                "alert_count": 1,
                "continuation_count": 0,
                "baseline_count": 0,
                "last_baseline_timestamp": None,
                "last_event_type": "MIGRATED",
                "last_move_from_alert_pct": 0,
            }
        )

        state[symbol] = previous_event
        save_state(state)

        return False

    # ==================================================
    # LAST ALERT CONTEXT
    # ==================================================

    last_alert_family = previous_event.get(
        "last_alert_signal_family"
    )

    if not last_alert_family:
        last_alert_family = _signal_family(
            signal_name=previous_event.get(
                "last_alert_signal_name"
            ),
            state=previous_event.get(
                "state"
            ),
        )

    last_alert_driver = (
        _normalize_driver(
            previous_event.get(
                "last_alert_driver"
            )
        )
    )

    move_from_last_alert_pct = (
        _move_from_last_alert(
            current_price,
            last_alert_price
        )
    )

    material_move = (
        abs(move_from_last_alert_pct)
        >= REPEAT_ALERT_MOVE_PCT
    )

    material_signal_change = (
        _material_signal_change(
            last_family=last_alert_family,
            new_family=current_family,
        )
    )

    material_driver_change = (
        _material_driver_change(
            last_driver=last_alert_driver,
            new_driver=current_driver,
        )
    )

    alert_count = int(
        previous_event.get(
            "alert_count",
            1
        )
    )

    # ==================================================
    # UPDATE LATEST OBSERVATION
    # ==================================================

    previous_event.update(
        {
            "state": new_state,
            "latest_date": current_date,
            "latest_price": current_price,
            "latest_change_pct": (
                current_change_pct
            ),
            "latest_rvol": current_rvol,
            "latest_price_activity_ratio": (
                current_price_activity_ratio
            ),
            "latest_signal_name": (
                current_signal_name
            ),
            "latest_driver": (
                current_driver
            ),
            "latest_signal_family": (
                current_family
            ),
            "baseline_count": 0,
            "last_baseline_timestamp": None,
            "last_move_from_alert_pct": (
                move_from_last_alert_pct
            ),
        }
    )

    # ==================================================
    # MATERIAL SIGNAL CHANGE
    # ==================================================

    if material_signal_change:
        alert_count += 1

        previous_event.update(
            {
                "last_alert_date": current_date,
                "last_alert_price": current_price,
                "last_alert_signal_name": (
                    current_signal_name
                ),
                "last_alert_driver": (
                    current_driver
                ),
                "last_alert_signal_family": (
                    current_family
                ),
                "alert_count": alert_count,
                "last_event_type": (
                    "SIGNAL_CHANGE"
                ),
            }
        )

        state[symbol] = previous_event
        save_state(state)

        return True

    # ==================================================
    # NEW DRIVER COMPONENT
    # ==================================================

    if material_driver_change:
        alert_count += 1

        previous_event.update(
            {
                "last_alert_date": current_date,
                "last_alert_price": current_price,
                "last_alert_signal_name": (
                    current_signal_name
                ),
                "last_alert_driver": (
                    current_driver
                ),
                "last_alert_signal_family": (
                    current_family
                ),
                "alert_count": alert_count,
                "last_event_type": (
                    "DRIVER_CHANGE"
                ),
            }
        )

        state[symbol] = previous_event
        save_state(state)

        return True

    # ==================================================
    # ±5% REPEAT ALERT
    # ==================================================

    if material_move:
        alert_count += 1

        previous_event.update(
            {
                "last_alert_date": current_date,
                "last_alert_price": current_price,
                "last_alert_signal_name": (
                    current_signal_name
                ),
                "last_alert_driver": (
                    current_driver
                ),
                "last_alert_signal_family": (
                    current_family
                ),
                "alert_count": alert_count,
                "last_event_type": (
                    "REPEAT_ALERT"
                ),
            }
        )

        state[symbol] = previous_event
        save_state(state)

        return True

    # ==================================================
    # SUPPRESSION
    # ==================================================

    previous_event[
        "last_event_type"
    ] = "SUPPRESSED"

    state[symbol] = previous_event
    save_state(state)

    return False
