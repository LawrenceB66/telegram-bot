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
            0 if participation_pct is None
            else float(participation_pct)
        )

        recent_change = (
            0 if recent_change is None
            else float(recent_change)
        )

        # --------------------------------------------------
        # STRUCTURAL RANKS
        # --------------------------------------------------

        volume_rank = {
            "NORMAL": 0,
            "ELEVATED": 1,
            "EXPANDING": 2,
            "SURGING": 3,
            "EXTREME": 4,
        }

        velocity_rank = {
            "NEGATIVE": -2,
            "REVERSING": -1,
            "MODERATE": 0,
            "BUILDING": 1,
            "ACCELERATING": 2,
            "EXTREME": 3,
            "STALLING": 0,
            "SLOWING": -1,
        }

        v_rank = volume_rank.get(volume, 0)
        vel_rank = velocity_rank.get(velocity, 0)

        # ==================================================
        # EXHAUSTION
        # ==================================================

        if (
            previous_state in ["LOADED", "EXTENDED"]
            and change_pct >= 10
            and v_rank >= 3
            and velocity in ["STALLING", "SLOWING"]
        ):
            return {
                "emoji": "⚠️",
                "name": "Exhaustion",
                "state": "EXHAUSTION",
                "volume": volume.title(),
                "driver": "Price Extension",
                "read": (
                    "Price remains extended while "
                    "participation begins slowing."
                ),
            }

        # ==================================================
        # MOMENTUM SURGE
        # ==================================================

        if (
            change_pct >= 10
            and v_rank >= 3
            and vel_rank >= 2
            and rvol >= 1.50
        ):
            return {
                "emoji": "💥",
                "name": "Momentum Surge",
                "state": "EXTENDED",
                "volume": volume.title(),
                "driver": "Price + Participation",
                "read": (
                    "Price and participation are "
                    "accelerating together."
                ),
            }

        # ==================================================
        # ACTIVE EXPANSION — STRONG
        # ==================================================

        if (
            change_pct >= 7
            and v_rank >= 2
            and vel_rank >= 2
            and rvol >= 1.00
        ):
            return {
                "emoji": "⚡",
                "name": "Active Expansion",
                "state": "LOADED",
                "volume": volume.title(),
                "driver": (
                    "Balanced Expansion"
                    if participation_pct >= 50
                    else "Price Led"
                ),
                "read": (
                    "Price and participation continue expanding."
                    if participation_pct >= 50
                    else "Price is advancing faster than participation."
                ),
            }

        # ==================================================
        # ACTIVE EXPANSION — BUILDING
        # ==================================================

        if (
            change_pct >= 5
            and v_rank >= 2
            and vel_rank >= 1
            and rvol >= 0.75
        ):
            return {
                "emoji": "⚡",
                "name": "Active Expansion",
                "state": "BUILDING",
                "volume": volume.title(),
                "driver": (
                    "Participation Led"
                    if participation_pct >= 50
                    else "Balanced Expansion"
                ),
                "read": (
                    "Participation is building ahead of price."
                    if participation_pct >= 50
                    else "Price and participation are improving together."
                ),
            }

        # ==================================================
        # PRESSURE BUILDING — RVOL LED
        # ==================================================

        if (
            abs(change_pct) < 5
            and rvol >= 2.25
            and v_rank >= 2
            and recent_change >= 0
        ):
            return {
                "emoji": "💣",
                "name": "Pressure Building",
                "state": "BUILDING",
                "volume": volume.title(),
                "driver": "Participation",
                "read": (
                    "Participation is elevated while "
                    "price remains contained."
                ),
            }

        # ==================================================
        # BREAKDOWN
        # ==================================================

        if (
            previous_state in ["BUILDING", "LOADED", "EXTENDED"]
            and change_pct < 2
            and v_rank >= 1
            and velocity in ["REVERSING", "NEGATIVE"]
        ):
            return {
                "emoji": "🔻",
                "name": "Breakdown",
                "state": "FAILURE",
                "volume": volume.title(),
                "driver": "Participation Fade",
                "read": (
                    "Participation is weakening as "
                    "price loses momentum."
                ),
            }

        # ==================================================
        # BASELINE
        # ==================================================

        return {
            "state": "BASELINE",
            "volume": volume.title(),
            "driver": None,
        }

    except Exception as e:
        print(f"Signal logic error: {e}")

        return {
            "state": "ERROR",
            "volume": "N/A",
            "driver": None,
        }
