# =========================
# SIGNAL LOGIC (WITH FILTER)
# =========================

def passes_quality_filter(signal, price_change, volume, velocity):
    """
    Selective Intelligence Layer
    Filters weak / noisy signals BEFORE alerting
    """

    # 🚫 Ignore weak downside moves
    if signal == "FAILURE" and abs(price_change) < 5:
        return False

    # 🚫 Ignore low participation
    if volume == "NORMAL":
        return False

    # 🚫 Ignore weak momentum
    if velocity in ["SLOW", "STALLING"]:
        return False

    return True


def classify_signal(price_change, volume, velocity):
    """
    Core signal classification (UNCHANGED STRUCTURE)
    """

    # 💣 TIME BOMB (LOADED)
    if price_change >= 5 and volume == "EXPANDING" and velocity == "ACCELERATING":
        return "LOADED", "💣"

    # 💣 TIME BOMB (EXTENDED)
    if price_change >= 8 and volume == "EXPANDING" and velocity == "EXTREME":
        return "EXTENDED", "💣"

    # 🔥 PRESSURE COOKER
    if price_change >= 3.5 and volume == "ELEVATED" and velocity == "BUILDING":
        return "BUILDING", "🔥"

    # ⚡ MOVERS
    if price_change >= 6 and volume == "SURGING" and velocity == "HIGH":
        return "EXPANSION", "⚡"

    # 🩸 BREAKDOWN
    if price_change <= -3.5 and volume == "ELEVATED" and velocity == "REVERSING":
        return "FAILURE", "🩸"

    # ⚠️ EXHAUSTION
    if price_change >= 10 and volume == "EXTREME" and velocity == "STALLING":
        return "EXHAUSTION", "⚠️"

    return None, None


def process_signal(symbol, price_change, volume, velocity):
    """
    FULL PIPELINE:
    classify → filter → return final signal
    """

    state, emoji = classify_signal(price_change, volume, velocity)

    if not state:
        return None

    # 🔒 APPLY FILTER HERE
    if not passes_quality_filter(state, price_change, volume, velocity):
        return None

    return {
        "symbol": symbol,
        "state": state,
        "emoji": emoji,
        "volume": volume,
        "velocity": velocity,
        "price_change": price_change
    }
