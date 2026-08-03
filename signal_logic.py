# ======================================================
# IAL SIGNAL CLASSIFICATION ENGINE
# REAL-TIME MARKET STRUCTURE ENGINE v2.3
#
# ENGINEERING PRINCIPLES
#
# • We do not predict. We classify.
# • Every market condition has one classification.
# • Every classification has one purpose.
# • Consistency creates trust.
# ======================================================

def classify_signal(price, change_pct, volume, velocity, previous_state=None):
    """
    Signal = State, not price alone.

    Required inputs:
    - price
    - change_pct
    - volume label / condition
    - velocity label / condition (internal use only)
    - previous_state
    """

    try:

        change_pct = float(change_pct)

        volume = str(volume).upper()
        velocity = str(velocity).upper()

        # ==================================================
        # 1. EXHAUSTION
        # Highest Priority
        # ==================================================

        if (
            change_pct >= 10
            and volume in ["EXTREME", "SURGING"]
            and velocity in ["STALLING", "SLOWING"]
        ):

            return {

                "emoji": "⚠️",

                "name": "Exhaustion",

                "state": "EXHAUSTION",

                "volume": "Extreme",

                "read":
                "Momentum slowing after sustained expansion."

            }

        # ==================================================
        # 2. MOMENTUM SURGE
        # ==================================================

        if (
            change_pct >= 10
            and volume in ["SURGING", "EXTREME"]
            and velocity in ["HIGH", "EXTREME"]
        ):

            return {

                "emoji": "💥",

                "name": "Momentum Surge",

                "state": "EXTENDED",

                "volume": "Expanding",

                "read":
                "Strong participation with accelerating pressure."

            }

        # ==================================================
        # 3. ACTIVE EXPANSION
        # Loaded Stage
        # ==================================================

        if (
            change_pct >= 7
            and volume in ["EXPANDING", "SURGING"]
            and velocity == "ACCELERATING"
        ):

            return {

                "emoji": "⚡",

                "name": "Active Expansion",

                "state": "LOADED",

                "volume": "Expanding",

                "read":
                "Pressure expanding with increasing participation."

            }

        # ==================================================
        # 4. ACTIVE EXPANSION
        # Building Stage
        # ==================================================

        if (
            change_pct >= 5
            and volume in ["EXPANDING", "SURGING"]
            and velocity == "BUILDING"
        ):

            return {

                "emoji": "⚡",

                "name": "Active Expansion",

                "state": "BUILDING",

                "volume": "Expanding",

                "read":
                "Pressure building with elevated participation."

            }

        # ==================================================
        # 5. BREAKDOWN
        # ==================================================

        if (
            previous_state in ["BUILDING", "LOADED", "EXTENDED"]
            and change_pct < 2
            and volume in [
                "ELEVATED",
                "EXPANDING",
                "SURGING",
                "EXTREME"
            ]
            and velocity in [
                "REVERSING",
                "NEGATIVE"
            ]
        ):

            return {

                "emoji": "🔻",

                "name": "Breakdown",

                "state": "FAILURE",

                "volume": "Elevated",

                "read":
                "Downside pressure increasing across structure."

            }

        # ==================================================
        # BASELINE
        # ==================================================

        return {

            "state": "BASELINE",

            "volume": volume.title()

        }

    except Exception as e:

        print(f"Signal logic error: {e}")

        return {

            "state": "ERROR",

            "volume": "N/A"

        }
