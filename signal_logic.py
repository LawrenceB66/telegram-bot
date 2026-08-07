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
            and rvol >= 1.50
            and v_rank >= 1
            and recent_change >= 0
        ):
            return {
                "emoji": "🔥",
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
