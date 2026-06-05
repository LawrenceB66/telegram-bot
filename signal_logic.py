# =========================
# SIGNAL CLASSIFICATION
# =========================

def classify_signal(price, change_pct, volume, velocity):
    try:
        # STATE LOGIC
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

        # RETURN AS DICTIONARY (CRITICAL FIX)
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
