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

                "read": "Price expansion is slowing while participation begins to fade."

            }

        # ==================================================
        # MOMENTUM SURGE
        # ==================================================

        if (
            change_pct >= 10
            and volume in ["SURGING", "EXTREME"]
            and velocity in ["EXTREME", "HIGH"]
        ):
            return {

                "emoji": "💥",

                "name": "Momentum Surge",

                "state": "EXTENDED",

                "volume": "Extreme",

                "read": "Price and participation are expanding together."

            }

        # ==================================================
        # ACTIVE EXPANSION
        # ==================================================

        if (
            change_pct >= 7
            and volume in ["SURGING", "EXPANDING"]
            and velocity in ["ACCELERATING", "HIGH", "EXTREME"]
        ):
            return {

                "emoji": "⚡",

                "name": "Active Expansion",

                "state": "LOADED",

                "volume": "Expanding",

                "read": "Price is expanding with improving participation."

            }

        # ==================================================
        # ACTIVE EXPANSION
        # ==================================================

        if (
            change_pct >= 5
            and volume in ["EXPANDING", "SURGING"]
            and velocity in ["BUILDING", "MODERATE"]
        ):
            return {

                "emoji": "⚡",

                "name": "Active Expansion",

                "state": "BUILDING",

                "volume": "Expanding",

                "read": "Participation is building behind the current price move."

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

                "read": "Participation is weakening as price loses momentum."

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
