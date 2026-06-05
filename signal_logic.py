# =========================
# IAL SIGNAL LOGIC (LOCKED)
# =========================

def classify_signal(price_change, rvol, velocity):
    """
    Returns:
    state, volume_label, velocity_label
    """

    # -------------------------
    # FAILURE (highest priority downside)
    # -------------------------
    if price_change < 0 and velocity == "REVERSING":
        return "FAILURE", "ELEVATED", "REVERSING"

    # -------------------------
    # EXHAUSTION
    # -------------------------
    if price_change >= 10 and velocity == "STALLING":
        return "EXHAUSTION", "EXTREME", "STALLING"

    # -------------------------
    # EXTENDED (post-expansion)
    # -------------------------
    if price_change >= 8 and rvol >= 2.5 and velocity == "EXTREME":
        return "EXTENDED", "EXPANDING", "EXTREME"

    # -------------------------
    # EXPANSION (event trigger)
    # -------------------------
    if price_change >= 6 and rvol >= 2.5 and velocity == "HIGH":
        return "EXPANSION", "SURGING", "HIGH"

    # -------------------------
    # LOADED (pre-expansion)
    # -------------------------
    if price_change >= 5 and rvol >= 2.0 and velocity == "ACCELERATING":
        return "LOADED", "EXPANDING", "ACCELERATING"

    # -------------------------
    # BUILDING (early pressure)
    # -------------------------
    if price_change >= 3.5 and rvol >= 1.5 and velocity == "BUILDING":
        return "BUILDING", "ELEVATED", "BUILDING"

    # -------------------------
    # BASELINE (no signal)
    # -------------------------
    return "BASELINE", None, None


# =========================
# EMOJI MAP (LOCKED)
# =========================

EMOJI_MAP = {
    "BUILDING": "🔥",
    "LOADED": "💣",
    "EXPANSION": "⚡️",
    "EXTENDED": "🚀",
    "EXHAUSTION": "⚠️",
    "FAILURE": "🩸"
}
