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

    return str(signal_name).strip().upper()


def _normalize_driver(driver):
    if not driver:
        return None

    driver = str(driver).strip().upper()

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
    """
    Converts the visible signal classification into a
    stable event family.

    State fallback keeps this file compatible until
    signal_name is handed in directly by bot.py.
    """

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

    if state_name == "OVERBOUGHT":
        return "EXHAUSTION"

    if state_name in {
        "DOWNSIDE",
        "BREAKDOWN",
    }:
        return "BREAKDOWN"

    return state_name or None


def _material_signal_change(
    last_family,
    new_family
):
    """
    Determines whether a classification transition is
    important enough to bypass the ±5% repeat gate.

    Ordinary internal state movement inside the same
    family is NOT alert-worthy.
    """

    if (
        not last_family
        or not new_family
        or last_family == new_family
    ):
        return False

    # Failure / reversal is always material.
    if new_family == "BREAKDOWN":
        return True

    # Recovery from downside into a constructive family
    # is also a meaningful regime transition.
    if (
        last_family == "BREAKDOWN"
        and new_family != "BREAKDOWN"
    ):
        return True

    # Exhaustion is materially different from expansion
    # or momentum and should be surfaced immediately.
    if new_family == "EXHAUSTION":
        return True

    # Price expansion emerging from contained pressure.
    if (
        last_family == "PRESSURE"
        and new_family in {
            "EXPANSION",
            "MOMENTUM",
        }
    ):
        return True

    # Momentum Surge is a true escalation from the lower
    # constructive families.
    if (
        new_family == "MOMENTUM"
        and last_family in {
            "PRESSURE",
            "EXPANSION",
        }
    ):
        return True

    return False


def seed_event(symbol, event):
    """
    Seed runtime state from reconstructed market history.
    """

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

    return event.get("state")


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
    }


def should_alert(
    symbol,
    new_state,
    trading_date=None,
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
            "latest_signal_name": current_signal_name,
            "latest_driver": current_driver,
            "latest_signal_family": current_family,
            "last_alert_signal_name": current_signal_name,
            "last_alert_driver": current_driver,
            "last_alert_signal_family": current_family,
            "alert_count": 1,
            "continuation_count": 0,
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
                "latest_change_pct": current_change_pct,
                "latest_rvol": current_rvol,
                "latest_price_activity_ratio": (
                    current_price_activity_ratio
                ),
                "latest_signal_name": current_signal_name,
                "latest_driver": current_driver,
                "latest_signal_family": current_family,
                "last_alert_signal_name": (
                    current_signal_name
                ),
                "last_alert_driver": current_driver,
                "last_alert_signal_family": (
                    current_family
                ),
                "alert_count": 1,
                "continuation_count": 0,
                "last_event_type": "MIGRATED",
                "last_move_from_alert_pct": 0,
            }
        )

        state[symbol] = previous_event
        save_state(state)

        return False

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

    new_session = (
        last_alert_date != current_date
    )

    alert_count = int(
        previous_event.get(
            "alert_count",
            1
        )
    )

    continuation_count = int(
        previous_event.get(
            "continuation_count",
            0
        )
    )

    previous_event.update(
        {
            "state": new_state,
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
            "latest_driver": current_driver,
            "latest_signal_family": (
                current_family
            ),
            "last_move_from_alert_pct": (
                move_from_last_alert_pct
            ),
        }
    )

    if material_signal_change:
        alert_count += 1

        if new_session:
            continuation_count += 1
            event_type = (
                "CONTINUATION_SIGNAL_CHANGE"
            )

        else:
            event_type = "SIGNAL_CHANGE"

        previous_event.update(
            {
                "last_alert_date": current_date,
                "last_alert_price": current_price,
                "last_alert_signal_name": (
                    current_signal_name
                ),
                "last_alert_driver": current_driver,
                "last_alert_signal_family": (
                    current_family
                ),
                "alert_count": alert_count,
                "continuation_count": (
                    continuation_count
                ),
                "last_event_type": event_type,
            }
        )

        state[symbol] = previous_event
        save_state(state)

        return True

    if material_move:
        alert_count += 1

        if new_session:
            continuation_count += 1
            event_type = "CONTINUATION"

        else:
            event_type = "REPEAT_ALERT"

        previous_event.update(
            {
                "last_alert_date": current_date,
                "last_alert_price": current_price,
                "last_alert_signal_name": (
                    current_signal_name
                ),
                "last_alert_driver": current_driver,
                "last_alert_signal_family": (
                    current_family
                ),
                "alert_count": alert_count,
                "continuation_count": (
                    continuation_count
                ),
                "last_event_type": event_type,
            }
        )

        state[symbol] = previous_event
        save_state(state)

        return True

    previous_event[
        "last_event_type"
    ] = "SUPPRESSED"

    state[symbol] = previous_event
    save_state(state)

    return False
