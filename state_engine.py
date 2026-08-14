import json
import os
from datetime import date


STATE_FILE = "state.json"

# Same-state repeat alerts require a material move
# from the LAST ALERTED PRICE.
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
    """
    Supports both:

    Legacy:
        "SNDK": "BUILDING"

    New:
        "SNDK": {
            "state": "BUILDING",
            ...
        }
    """

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
    """
    Provides alert metadata for bot.py / send_alert.py.
    """

    event = get_previous_event(symbol)

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
    }


def should_alert(
    symbol,
    new_state,
    trading_date=None,
    price=None,
    change_pct=None,
    rvol=None,
    price_activity_ratio=None,
):
    """
    EVENT MEMORY RULES

    FIRST QUALIFYING EVENT
    -> Alert #1

    SAME STATE + +/-5% MOVE FROM LAST ALERTED PRICE
    -> Alert again
    -> 2nd Alert / 3rd Alert / 4th Alert...

    SAME STATE + NEW SESSION + MATERIAL MOVE
    -> Continuation alert

    SAME STATE + INSUFFICIENT MOVE
    -> Suppress
    -> Keep measuring from the last ALERTED price

    STATE CHANGE
    -> Alert immediately
    -> Preserve event history
    """

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

    # ==================================================
    # FIRST QUALIFYING EVENT
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
            "alert_count": 1,
            "continuation_count": 0,
            "last_event_type": "NEW_EVENT",
            "last_move_from_alert_pct": 0,
        }

        save_state(state)
        return True

    last_state = previous_event.get(
        "state"
    )

    last_alert_date = previous_event.get(
        "last_alert_date"
    )

    last_alert_price = previous_event.get(
        "last_alert_price"
    )

    # ==================================================
    # LEGACY MIGRATION
    #
    # Convert old string-only state into event memory.
    # Do not generate a false repeat alert.
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
                "latest_change_pct": current_change_pct,
                "latest_rvol": current_rvol,
                "latest_price_activity_ratio": (
                    current_price_activity_ratio
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

    new_session = (
        last_alert_date != current_date
    )

    state_changed = (
        last_state != new_state
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

    # ==================================================
    # ALWAYS UPDATE LATEST OBSERVATION
    # ==================================================

    previous_event["latest_date"] = (
        current_date
    )

    previous_event["latest_price"] = (
        current_price
    )

    previous_event["latest_change_pct"] = (
        current_change_pct
    )

    previous_event["latest_rvol"] = (
        current_rvol
    )

    previous_event[
        "latest_price_activity_ratio"
    ] = current_price_activity_ratio

    previous_event[
        "last_move_from_alert_pct"
    ] = move_from_last_alert_pct

    # ==================================================
    # STATE CHANGE
    #
    # New classification is automatically alert-worthy.
    # ==================================================

    if state_changed:
        alert_count += 1

        if new_session:
            continuation_count += 1
            event_type = (
                "CONTINUATION_STATE_CHANGE"
            )

        else:
            event_type = (
                "STATE_CHANGE"
            )

        previous_event.update(
            {
                "state": new_state,
                "last_alert_date": current_date,
                "last_alert_price": current_price,
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

    # ==================================================
    # SAME STATE + MATERIAL MOVE
    #
    # Direction does not matter.
    #
    # +5% from last alert -> repeat
    # -5% from last alert -> repeat
    #
    # The signal must already be qualifying because
    # should_alert() is only called after classification.
    # ==================================================

    if material_move:
        alert_count += 1

        if new_session:
            continuation_count += 1
            event_type = "CONTINUATION"

        else:
            event_type = "REPEAT_ALERT"

        previous_event.update(
            {
                "state": new_state,
                "last_alert_date": current_date,
                "last_alert_price": current_price,
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

    # ==================================================
    # SAME STATE + INSUFFICIENT MOVE
    #
    # Do NOT move last_alert_price.
    #
    # This is critical:
    # the next scan continues measuring from the price
    # actually shown to the Telegram room.
    # ==================================================

    previous_event["state"] = (
        new_state
    )

    previous_event["last_event_type"] = (
        "SUPPRESSED"
    )

    state[symbol] = previous_event
    save_state(state)

    return False
