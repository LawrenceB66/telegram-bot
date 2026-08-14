"price_activity_ratio": price_activity_ratio,
            "event_start_date": current_date,
            "event_start_price": price,
            "continuation_count": 0,
            "last_event_type": "NEW_STATE",
        }

        save_state(state)
        return True

    # ==================================================
    # LEGACY MIGRATION
    # ==================================================

    if last_date is None:
        state[symbol] = {
            "state": new_state,
            "date": current_date,
            "price": price,
            "change_pct": change_pct,
            "rvol": rvol,
            "price_activity_ratio": price_activity_ratio,
            "event_start_date": current_date,
            "event_start_price": price,
            "continuation_count": 0,
            "last_event_type": "MIGRATED",
        }

        save_state(state)
        return False

    # ==================================================
    # CROSS-SESSION CONTINUATION
    # ==================================================

    if last_date != current_date:
        continuation_count = (
            int(previous_event.get("continuation_count", 0)) + 1
        )

        state[symbol] = {
            "state": new_state,
            "date": current_date,
            "price": price,
            "change_pct": change_pct,
            "rvol": rvol,
            "price_activity_ratio": price_activity_ratio,
            "event_start_date": (
                previous_event.get("event_start_date") or last_date
            ),
            "event_start_price": (
                previous_event.get("event_start_price")
                if previous_event.get("event_start_price") is not None
                else previous_event.get("price")
            ),
            "continuation_count": continuation_count,
            "last_event_type": "CONTINUATION",
        }

        save_state(state)
        return True

    # ==================================================
    # SAME-SESSION DUPLICATE
    # ==================================================

    previous_event["price"] = price
    previous_event["change_pct"] = change_pct
    previous_event["rvol"] = rvol
    previous_event["price_activity_ratio"] = price_activity_ratio
    previous_event["last_event_type"] = "DUPLICATE"

    state[symbol] = previous_event
    save_state(state)

    return False
