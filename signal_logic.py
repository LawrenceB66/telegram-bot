# =========================
# SIGNAL CLASSIFICATION ENGINE
# =========================

BUILDING_THRESHOLD = 0
LOADED_THRESHOLD = 1
EXPANSION_THRESHOLD = 3.5
EXTENDED_THRESHOLD = 6
FAILURE_THRESHOLD = -3


def classify_signal(price, change_pct, volume, velocity):
    try:
        change_pct = float(change_pct)

        # =========================
        # STATE CLASSIFICATION
        # =========================

        if change_pct >= EXTENDED_THRESHOLD:
            state = "EXTENDED"
        elif change_pct >= EXPANSION_THRESHOLD:
            state = "EXPANSION"
        elif change_pct > LOADED_THRESHOLD:
            state = "LOADED"
        elif change_pct > BUILDING_THRESHOLD:
            state = "BUILDING"
        elif change_pct <= FAILURE_THRESHOLD:
            state = "FAILURE"
        else:
            state = "EXHAUSTION"

        # =========================
        # RETURN STRUCTURED OBJECT
        # =========================

        return {
            "state": state,
            "volume": volume,
            "velocity": velocity
        }

    except Exception as e:
        print(f"Signal logic error: {e}")
        return {
            "state": "ERROR",
            "volume": "N/A",
            "velocity": "N/A"
        }
