# ======================================================
# IAL SIGNAL CLASSIFICATION ENGINE
# REAL-TIME MARKET STRUCTURE ENGINE v2.2
# Bullish Hierarchy Calibration
# ======================================================

def classify_signal(price, change_pct, volume, velocity, previous_state=None):
    """
    Signal = State, not price alone.

    Required inputs:
    - price
    - change_pct
    - volume label / condition
    - velocity label / condition
    - previous_state for breakdown validation
    """

    try:
        change_pct = float(change_pct)

        volume = str(volume).upper()
        velocity = str(velocity).upper()

        # =========================
        # 1. EXHAUSTION
        # Highest Priority
        # =========================

        if (
            change_pct >= 10
            and volume in ["EXTREME", "SURGING"]
            and velocity in ["STALLING", "SLOWING"]
        ):
            return {
                "emoji": "⚠️",
                "name": "EXHAUSTION",
                "state": "EXHAUSTION",
                "volume": "EXTREME",
                "velocity": "STALLING",
                "read": "Momentum slowing after sustained expansion."
            }

        # =========================
        # 2. MOMENTUM SURGE
        # =========================

        if (
            change_pct >= 10
            and volume in ["SURGING", "EXTREME"]
            and velocity in ["HIGH", "EXTREME"]
        ):
            return {
                "emoji": "💥",
                "name": "MOMENTUM SURGE",
                "state": "EXTENDED",
                "volume": "EXPANDING",
                "velocity": "EXTREME",
                "read": "Strong participation with accelerating pressure."
            }

        # =========================
        # 3. ACTIVE EXPANSION
        # =========================

        if (
            change_pct >= 7
            and volume in ["EXPANDING", "SURGING"]
            and velocity == "ACCELERATING"
        ):
            return {
                "emoji": "⚡",
                "name": "ACTIVE EXPANSION",
                "state": "LOADED",
                "volume": "EXPANDING",
                "velocity": "ACCELERATING",
                "read": "Pressure expanding with increasing participation."
            }

        # =========================
        # 4. ACTIVE EXPANSION
        # Early Stage
        # =========================

        if (
            change_pct >= 5
            and volume in ["EXPANDING", "SURGING"]
            and velocity == "BUILDING"
        ):
            return {
                "emoji": "⚡",
                "name": "ACTIVE EXPANSION",
                "state": "BUILDING",
                "volume": "EXPANDING",
                "velocity": "BUILDING",
                "read": "Pressure building with elevated participation."
            }

        # =========================
        # 5. BREAKDOWN
        # =========================

        if (
            previous_state in ["BUILDING", "LOADED", "EXTENDED"]
            and change_pct < 2
            and volume in ["ELEVATED", "EXPANDING", "SURGING", "EXTREME"]
            and velocity in ["REVERSING", "NEGATIVE"]
        ):
            return {
                "emoji": "🔻",
                "name": "BREAKDOWN",
                "state": "FAILURE",
                "volume": "ELEVATED",
                "velocity": "REVERSING",
                "read": "Downside pressure increasing across structure."
            }

        # =========================
        # BASELINE
        # =========================

        return {
            "state": "BASELINE",
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
