def classify_signal(price, change_pct, volume, velocity, previous_state=None):

    try:

        change_pct = float(change_pct)

        volume = str(volume).upper()
        velocity = str(velocity).upper()

        # ==================================================
        # EXHAUSTION
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

                "read": "Momentum slowing after sustained expansion."

            }

        # ==================================================
        # MOMENTUM SURGE
        # ==================================================

        if (
            change_pct >= 10
            and volume == "EXTREME"
            and velocity == "EXTREME"
        ):
            return {

                "emoji": "💥",

                "name": "Momentum Surge",

                "state": "EXTENDED",

                "volume": "Extreme",

                "read": "Strong participation with accelerating pressure."

            }

        # ==================================================
        # ACTIVE EXPANSION
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

                "read": "Pressure expanding with increasing participation."

            }

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

                "read": "Pressure building with elevated participation."

            }

        # ==================================================
        # BREAKDOWN
        # ==================================================

        if (
            previous_state in ["BUILDING", "LOADED", "EXTENDED"]
            and change_pct < 2
            and volume in ["ELEVATED", "EXPANDING", "SURGING", "EXTREME"]
            and velocity in ["REVERSING", "NEGATIVE"]
        ):
            return {

                "emoji": "🔻",

                "name": "Breakdown",

                "state": "FAILURE",

                "volume": "Elevated",

                "read": "Downside pressure increasing across structure."

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
