# =========================
# SIGNAL LOGIC (CLEAN BUILD)
# =========================

def classify_signal(price, percent_change, volume, avg_volume, velocity):

    # -------------------------
    # FORCE DATA TYPES (CRITICAL FIX)
    # -------------------------
    try:
        price = float(price)
        percent_change = float(percent_change)
        volume = float(volume)
        avg_volume = float(avg_volume)
    except:
        return None  # skip bad data safely

    # -------------------------
    # RVOL CALC (TEMP BASE)
    # -------------------------
    if avg_volume == 0:
        rvol = 0
    else:
        rvol = volume / avg_volume

    # -------------------------
    # PRIORITY LOGIC (LOCKED)
    # -------------------------

    # 💣 EXTENDED
    if percent_change >= 8 and rvol >= 2.5 and velocity == "EXTREME":
        return {
            "emoji": "💣",
            "state": "EXTENDED",
            "volume": "EXPANDING",
            "velocity": "EXTREME"
        }

    # 💣 LOADED
    if percent_change >= 5 and rvol >= 2.0 and velocity in ["ACCELERATING", "HIGH"]:
        return {
            "emoji": "💣",
            "state": "LOADED",
            "volume": "EXPANDING",
            "velocity": "ACCELERATING"
        }

    # ⚡ EXPANSION
    if percent_change >= 6 and rvol >= 2.5 and velocity == "HIGH":
        return {
            "emoji": "⚡️",
            "state": "EXPANSION",
            "volume": "SURGING",
            "velocity": "HIGH"
        }

    # 🔥 BUILDING
    if percent_change >= 3.5 and rvol >= 1.5 and velocity == "MODERATE":
        return {
            "emoji": "🔥",
            "state": "BUILDING",
            "volume": "ELEVATED",
            "velocity": "BUILDING"
        }

    # 🩸 FAILURE
    if percent_change < 2:
        return {
            "emoji": "🩸",
            "state": "FAILURE",
            "volume": "ELEVATED",
            "velocity": "REVERSING"
        }

    # ⚠️ EXHAUSTION
    if percent_change >= 10 and rvol >= 3 and velocity == "STALLING":
        return {
            "emoji": "⚠️",
            "state": "EXHAUSTION",
            "volume": "EXTREME",
            "velocity": "STALLING"
        }
