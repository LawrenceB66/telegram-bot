def classify_signal(symbol, pct, structure):

    if not structure:
        return None

    rvol = structure.get("rvol", 0)
    velocity = structure.get("velocity", "LOW")

    # TIME BOMB EXTENDED
    if pct >= 8 and rvol >= 2.5 and velocity == "EXTREME":
        return {
            "emoji": "💣",
            "name": "Ticking Time Bomb",
            "volume": "EXPANDING",
            "velocity": "EXTREME",
            "state": "EXTENDED",
            "read": "Pressure has fully expanded. The move is extended with high momentum. Volatility is elevated. Proceed with caution."
        }

    # TIME BOMB LOADED
    if pct >= 5 and rvol >= 2.0 and velocity == "ACCELERATING":
        return {
            "emoji": "💣",
            "name": "Ticking Time Bomb",
            "volume": "EXPANDING",
            "velocity": "ACCELERATING",
            "state": "LOADED",
            "read": "Pressure conditions are actively expanding. Volume and momentum are aligned. Setup is unstable and may accelerate."
        }

    # MOVERS
    if pct >= 6 and rvol >= 2.5 and velocity == "HIGH":
        return {
            "emoji": "⚡️",
            "name": "Movers",
            "volume": "SURGING",
            "velocity": "HIGH",
            "state": "EXPANSION",
            "read": "Strong directional movement confirmed. Volume and momentum are aligned. This is an active expansion phase."
        }

    # PRESSURE COOKER
    if pct >= 3.5 and rvol >= 1.5 and velocity == "MODERATE":
        return {
            "emoji": "🔥",
            "name": "Pressure Cooker",
            "volume": "ELEVATED",
            "velocity": "BUILDING",
            "state": "BUILDING",
            "read": "Pressure is building beneath the surface. Volume is increasing while price remains controlled. Early stage setup. Attention required."
        }

    # BREAKDOWN
    if pct < 2 and velocity == "REVERSING":
        return {
            "emoji": "🩸",
            "name": "Breakdown",
            "volume": "ELEVATED",
            "velocity": "REVERSING",
            "state": "FAILURE",
            "read": "Momentum is breaking down. The move is losing structure under pressure. This may signal a failed setup or unwind."
        }

    # EXHAUSTION
    if pct >= 10 and rvol >= 3.0 and velocity == "STALLING":
        return {
            "emoji": "⚠️",
            "name": "Exhaustion",
            "volume": "EXTREME",
            "velocity": "STALLING",
            "state": "EXHAUSTION",
            "read": "The move is extended and momentum is slowing. This is not a new setup. Risk of reversal or consolidation is increasing."
        }

    return None
