def classify_signal(price, change_pct, volume, velocity, previous_state=None):

    try:

        change_pct = float(change_pct)

        volume = str(volume).upper()
        velocity = str(velocity).upper()

        # ==================================================
        # EXHAUSTION
        # ==================================================

        if (
            previous_state in ["LOADED", "EXTENDED"]
            and change_pct >= 10
            and volume == "EXTREME"
            and velocity in ["STALLING", "SLOWING"]
        ):
            return {

                "emoji": "⚠️",

                "name": "Exhaustion",

                "state": "EXHAUSTION",

                "volume": "Extreme",

                "read": "Price remains extended while participation begins slowing."

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

                "read": "Price and participation are accelerating together."

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

                "read": "Price is advancing with improving participation."

            }

        # ==================================================
        # ACTIVE EXPANSION
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

                "read": "Participation is strengthening behind the current move."

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

                "read": "Price is weakening while participation continues to deteriorate."

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
