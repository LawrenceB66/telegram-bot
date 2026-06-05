# =========================
# SIGNAL CLASSIFICATION ENGINE
# =========================

def classify_signal(price, change_pct, volume, velocity):
    try:
        # =========================
        # STATE CLASSIFICATION
        # =========================

        if change_pct >= 6:
            state = "EXTENDED"
        elif change_pct >= 3.5:
            state = "EXPANSION"
        elif change_pct > 1:
            state = "LOADED"
        elif change_pct > 0:
            state = "BUILDING"
        elif change_pct < -3:
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
