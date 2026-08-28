def classify_signal(
    price,
    change_pct,
    volume,
    velocity,
    previous_state=None,
    rvol=None,
    participation_pct=None,
    recent_change=None,
    price_activity_ratio=None,
    drawdown_from_high_pct=None,
    rebound_from_low_pct=None
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

        drawdown_from_high_pct = (
            0
            if drawdown_from_high_pct is None
            else float(drawdown_from_high_pct)
        )

        rebound_from_low_pct = (
            0
            if rebound_from_low_pct is None
            else float(rebound_from_low_pct)
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

        material_intraday_reversal = (
            drawdown_from_high_pct <= -5
        )

        near_session_low = (
            rebound_from_low_pct <= 2
        )

        # ==================================================
        # BREAKDOWN
        # ==================================================

        path_breakdown = (
            material_intraday_reversal
            and near_session_low
            and rvol >= 1.50
            and v_rank >= 1
            and price_activity_ratio >= 1.00
        )

        state_breakdown = (
            previous_state in [
                "BUILDING",
                "LOADED",
                "EXTENDED",
                "STALL"
            ]
            and change_pct < 2
            and rvol >= 1.50
            and v_rank >= 1
            and price_activity_ratio >= 1.00
            and velocity in [
                "REVERSING",
                "NEGATIVE"
            ]
        )

        if (
            path_breakdown
            or state_breakdown
        ):
            return {
                "emoji": "🔻",
                "name": "Breakdown",
                "state": "FAILURE",
                "volume": volume.title(),
                "driver": "PRICE + VOLUME",
                "read": (
                    "Price weakening while "
                    "participation remains elevated."
                ),
            }

        # ==================================================
        # PRICE STALL
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
            and not material_intraday_reversal
        ):
            return {
                "emoji": "⚠️",
                "name": "Price Stall",
                "state": "STALL",
                "volume": volume.title(),
                "driver": "PRICE + VOLUME",
                "read": (
                    "Price paused; participation "
                    "remains elevated."
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
            and not material_intraday_reversal
        ):
            return {
                "emoji": "💥",
                "name": "Momentum Surge",
                "state": "EXTENDED",
                "volume": volume.title(),
                "driver": "PRICE + VOLUME",
                "read": (
                    "Price and participation "
                    "expanding together."
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
            and not material_intraday_reversal
        ):
            return {
                "emoji": "⚡",
                "name": "Active Expansion",
                "state": "LOADED",
                "volume": volume.title(),
                "driver": "PRICE + VOLUME",
                "read": (
                    "Price activity expanding "
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
            and not material_intraday_reversal
        ):
            return {
                "emoji": "⚡",
                "name": "Active Expansion",
                "state": "BUILDING",
                "volume": volume.title(),
                "driver": "PRICE + VOLUME",
                "read": (
                    "Price activity expanding "
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
            and not material_intraday_reversal
        ):
            return {
                "emoji": "💣",
                "name": "Pressure Building",
                "state": "BUILDING",
                "volume": volume.title(),
                "driver": "VOLUME",
                "read": (
                    "Participation elevated while "
                    "price activity remains contained."
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
