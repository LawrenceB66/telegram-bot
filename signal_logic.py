# =========================
# IAL SIGNAL CLASSIFICATION ENGINE
# REAL-TIME MARKET STRUCTURE ENGINE v1.0
# =========================

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
        # 1. MOMENTUM SURGE
        # Highest Priority
        # =========================

        if (
            change_pct >= 8
            and volume in ["EXPANDING", "EXTREME", "SURGING"]
            and velocity in ["EXTREME", "HIGH"]
        ):
            return {
                "emoji": "💥",
                "name": "MOMENTUM SURGE",
                "state": "EXTENDED",
                "volume": "EXPANDING",
                "velocity": "EXTREME",
                "read": "Surge confirmed with explosive participation and acceleration."
            }

        # =========================
        # 2. ACTIVE EXPANSION
        # =========================

        if (
            change_pct >= 5
            and volume in ["EXPANDING", "SURGING"]
            and velocity in ["ACCELERATING", "HIGH", "EXTREME"]
        ):
            return {
                "emoji": "⚡",
                "name": "ACTIVE EXPANSION",
                "state": "LOADED",
                "volume": "EXPANDING",
                "velocity": "ACCELERATING",
                "read": "Expansion confirmed with increased participation."
            }

        # =========================
        # 3. EXHAUSTION
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
                "read": "Potential trend fatigue; watch for reversal or pause as participation wanes."
            }

        # =========================
        # 4. ACTIVE EXPANSION
        # Early Stage
        # =========================

        if (
            change_pct >= 3.5
            and volume in ["ELEVATED", "EXPANDING", "SURGING"]
            and velocity in ["BUILDING", "MODERATE"]
        ):
            return {
                "emoji": "⚡",
                "name": "ACTIVE EXPANSION",
                "state": "BUILDING",
                "volume": "ELEVATED",
                "velocity": "BUILDING",
                "read": "Expansion confirmed with increased participation."
            }

        # =========================
        # 5. MOMENTUM SURGE
        # =========================

        if (
            change_pct >= 6
            and volume in ["SURGING", "EXPANDING"]
            and velocity == "HIGH"
        ):
            return {
                "emoji": "💥",
                "name": "MOMENTUM SURGE",
                "state": "EXPANSION",
                "volume": "SURGING",
                "velocity": "HIGH",
                "read": "Surge confirmed with explosive participation and acceleration."
            }

        # =========================
        # 6. BREAKDOWN
        # =========================

        if (
            previous_state in ["BUILDING", "LOADED", "EXPANSION", "EXTENDED"]
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
                "read": "Trend deterioration confirmed; selling participation increasing with downward acceleration."
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
