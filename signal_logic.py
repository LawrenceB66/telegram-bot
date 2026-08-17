def classify_signal(
    price,
    change_pct,
    volume,
    velocity,
    previous_state=None,
    rvol=None,
    participation_pct=None,
    recent_change=None,
    price_activity_ratio=None
):
    try:
        change_pct = float(change_pct)
        volume = str(volume).upper()
        velocity = str(velocity).upper()

        rvol = (
            0
            if rvol is None
            else float(rvol)
        )

        participation_pct = (
            0
            if participation_pct is None
            else float(participation_pct)
        )

        recent_change = (
            0
            if recent_change is None
            else float(recent_change)
        )

        price_activity_ratio = (
            0
            if price_activity_ratio is None
            else float(price_activity_ratio)
        )

        # --------------------------------------------------
        # STRUCTURAL RANKS
        # --------------------------------------------------

        volume_rank = {
            "NORMAL": 0,
            "ELEVATED": 1,
            "EXPANDED": 2,
            "SIGNIFICANT EXPANSION": 3,
            "EXTREME": 4,
        }

        velocity_rank = {
            "NEGATIVE": -2,
            "REVERSING": -1,
            "SLOWING": -1,
            "MODERATE": 0,
            "STALLING": 0,
            "BUILDING": 1,
            "HIGH": 1,
            "ACCELERATING": 2,
            "EXTREME": 3,
        }

        v_rank = volume_rank.get(
            volume,
            0
        )

        vel_rank = velocity_rank.get(
            velocity,
            0
        )

        # ==================================================
        # EXHAUSTION
        # ==================================================

        if (
            previous_state in [
                "LOADED",
                "EXTENDED"
            ]
            and change_pct >= 10
            and rvol >= 2.50
            and v_rank >= 3
            and price_activity_ratio >= 1.50
            and velocity in [
                "STALLING",
                "SLOWING"
            ]
        ):
            return {
                "emoji": "⚠️",
                "name": "Exhaustion",
                "state": "EXHAUSTION",
                "volume": volume.title(),
                "driver": "PRICE",
                "read": (
                    "Price remains extended while "
                    "immediate momentum begins slowing."
                ),
            }

        # ==================================================
        # MOMENTUM SURGE
        # ==================================================

        if (
            change_pct >= 10
            and rvol >= 2.50
            and v_rank >= 3
            and price_activity_ratio >= 1.50
            and vel_rank >= 2
        ):
            return {
                "emoji": "💥",
                "name": "Momentum Surge",
                "state": "EXTENDED",
                "volume": volume.title(),
                "driver": "PRICE + VOLUME",
                "read": (
                    "Price activity and participation "
                    "are expanding together."
                ),
            }

        # ==================================================
        # ACTIVE EXPANSION — STRONG
        # ==================================================

        if (
            change_pct >= 7
            and rvol >= 2.00
            and v_rank >= 2
            and price_activity_ratio >= 1.25
            and vel_rank >= 2
        ):
            return {
                "emoji": "⚡",
                "name": "Active Expansion",
                "state": "LOADED",
                "volume": volume.title(),
                "driver": "PRICE + VOLUME",
                "read": (
                    "Price activity is expanding "
                    "with elevated participation."
                ),
            }

        # ==================================================
        # ACTIVE EXPANSION — BUILDING
        # ==================================================

        if (
            change_pct >= 5
            and rvol >= 1.50
            and v_rank >= 1
            and price_activity_ratio >= 1.00
            and vel_rank >= 1
        ):
            return {
                "emoji": "⚡",
                "name": "Active Expansion",
                "state": "BUILDING",
                "volume": volume.title(),
                "driver": "PRICE + VOLUME",
                "read": (
                    "Price activity is expanding "
                    "with elevated participation."
                ),
            }

        # ==================================================
        # PRESSURE BUILDING
        # ==================================================

        if (
            abs(change_pct) < 5
            and rvol >= 3.00
            and v_rank >= 4
            and 0 < price_activity_ratio <= 1.00
            and recent_change >= 0
        ):
            return {
                "emoji": "💣",
                "name": "Pressure Building",
                "state": "BUILDING",
                "volume": volume.title(),
                "driver": "VOLUME",
                "read": (
                    "Participation is elevated while "
                    "price activity remains contained."
                ),
            }

        # ==================================================
        # BREAKDOWN
        # ==================================================

        if (
            previous_state in [
                "BUILDING",
                "LOADED",
                "EXTENDED"
            ]
            and change_pct < 2
            and rvol >= 1.50
            and v_rank >= 1
            and price_activity_ratio >= 1.00
            and velocity in [
                "REVERSING",
                "NEGATIVE"
            ]
        ):
            return {
                "emoji": "🔻",
                "name": "Breakdown",
                "state": "FAILURE",
                "volume": volume.title(),
                "driver": "PRICE",
                "read": (
                    "Price activity is expanding lower "
                    "while participation remains elevated."
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
        print(
            f"Signal logic error: {e}"
        )

        return {
            "state": "ERROR",
            "volume": "N/A",
            "driver": None,
        }
