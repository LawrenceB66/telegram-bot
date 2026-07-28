# =========================
# IAL SIGNAL CLASSIFICATION ENGINE
# GLOBAL SIGNAL STRUCTURE v3.0 LOCKED BASELINE
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
        # 1. TICKING TIME BOMB — EXTENDED
        # Priority: highest
        # =========================

        if (
            change_pct >= 8
            and volume in ["EXPANDING", "EXTREME", "SURGING"]
            and velocity in ["EXTREME", "HIGH"]
        ):
            return {
                "emoji": "💥",
                "name": "Ticking Time Bomb",
                "state": "EXTENDED",
                "volume": "EXPANDING",
                "velocity": "EXTREME",
                "read": "Pressure has fully expanded. Elevated volatility warrants caution."
            }

        # =========================
        # 2. TICKING TIME BOMB — LOADED
        # =========================

        if (
            change_pct >= 5
            and volume in ["EXPANDING", "SURGING"]
            and velocity in ["ACCELERATING", "HIGH", "EXTREME"]
        ):
            return {
                "emoji": "💣",
                "name": "Ticking Time Bomb",
                "state": "LOADED",
                "volume": "EXPANDING",
                "velocity": "ACCELERATING",
                "read": "Pressure has entered an active expansion phase. Monitor for continuation."
            }

        # =========================
        # 3. EXHAUSTION — NON-PRIMARY CAUTION STATE
        # =========================

        if (
            change_pct >= 10
            and volume in ["EXTREME", "SURGING"]
            and velocity in ["STALLING", "SLOWING"]
        ):
            return {
                "emoji": "⚠️",
                "name": "Exhaustion",
                "state": "EXHAUSTION",
                "volume": "EXTREME",
                "velocity": "STALLING",
                "read": "The move is extended and momentum is slowing. This is not a new setup — risk of reversal or consolidation is increasing."
            }

        # =========================
        # 4. PRESSURE COOKER
        # =========================

        if (
            change_pct >= 3.5
            and volume in ["ELEVATED", "EXPANDING", "SURGING"]
            and velocity in ["BUILDING", "MODERATE"]
        ):
            return {
                "emoji": "🔥",
                "name": "Pressure Cooker",
                "state": "BUILDING",
                "volume": "ELEVATED",
                "velocity": "BUILDING",
                "read": "Pressure is building beneath the surface. Volume is increasing while price remains controlled. Early-stage setup — attention required."
            }

        # =========================
        # 5. MOVERS
        # Does NOT override Time Bomb
        # =========================

        if (
            change_pct >= 6
            and volume in ["SURGING", "EXPANDING"]
            and velocity == "HIGH"
        ):
            return {
                "emoji": "⚡️",
                "name": "Movers",
                "state": "EXPANSION",
                "volume": "SURGING",
                "velocity": "HIGH",
                "read": "Strong directional movement confirmed. Volume and momentum are aligned. This is an active expansion phase."
            }

        # =========================
        # 6. BREAKDOWN
        # Requires previous strength
        # =========================

        if (
            previous_state in ["BUILDING", "LOADED", "EXPANSION", "EXTENDED"]
            and change_pct < 2
            and volume in ["ELEVATED", "EXPANDING", "SURGING", "EXTREME"]
            and velocity in ["REVERSING", "NEGATIVE"]
        ):
            return {
                "emoji": "🩸",
                "name": "Breakdown",
                "state": "FAILURE",
                "volume": "ELEVATED",
                "velocity": "REVERSING",
                "read": "Momentum is breaking down. The move is losing structure under pressure. This may signal a failed setup or unwind."
            }

        # =========================
        # 7. BASELINE — NO ALERT
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
