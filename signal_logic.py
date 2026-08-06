def classify_signal(
    price,
    change_pct,
    volume,
    velocity,
    previous_state=None,
    rvol=None,
    participation_pct=None,
    recent_change=None
):

    try:

        change_pct = float(change_pct)

        volume = str(volume).upper()
        velocity = str(velocity).upper()

        rvol = 0 if rvol is None else float(rvol)
        participation_pct = (
            0 if participation_pct is None else float(participation_pct)
        )
        recent_change = (
            0 if recent_change is None else float(recent_change)
        )

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

                "driver": "Price Extension",

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

                "driver": "Price + Participation",

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

                "driver": (
                    "Balanced Expansion"
                    if participation_pct >= 50
                    else "Price Led"
                ),

                "read": (
                    "Price and participation continue expanding."
                    if participation_pct >= 50
                    else "Price is advancing faster than participation."
                )

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

                "driver": (
                    "Participation Led"
                    if participation_pct >= 50
                    else "Balanced Expansion"
                ),

                "read": (
                    "Participation is building ahead of price."
                    if participation_pct >= 50
                    else "Price and participation are improving together."
                )

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

                "driver": "Participation Fade",

                "read": "Participation is weakening as price loses momentum."

            }

        # ==================================================
        # BASELINE
        # ==================================================

        return {

            "state": "BASELINE",

            "volume": volume.title(),

            "driver": None

        }

    except Exception as e:

        print(f"Signal logic error: {e}")

        return {

            "state": "ERROR",

            "volume": "N/A",

            "driver": None

        }
