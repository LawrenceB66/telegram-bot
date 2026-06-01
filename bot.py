import requests
import time
import os
import json

from send_alert import send_alert

# =========================
# CONFIG
# =========================

CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

CHECK_INTERVAL = 30
COOLDOWN_SECONDS = 300

STATE_FILE = "state.json"

TICKERS = [
    "AMC","GME","CVNA","UPST","LCID","RIVN","NIO","XPEV","PLTR","AI",
    "SOFI","HOOD","AFRM","DKNG","OPEN","QS","MARA","RIOT","COIN","SNDL",
    "TLRY","FUBO","NKLA","FFIE","MULN","SINT","WOK"
]

# =========================
# LOAD / SAVE STATE
# =========================

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# =========================
# DATA FETCH
# =========================

def get_price_data(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()

        price = data.get("c")
        prev_close = data.get("pc")

        if not price or not prev_close:
            return None

        change_pct = ((price - prev_close) / prev_close) * 100

        return {
            "price": round(price, 2),
            "change_pct": round(change_pct, 2)
        }

    except:
        return None

# =========================
# STRUCTURE FETCH (STRICT)
# =========================

def get_structure(symbol):
    """
    STRICT MODE:
    If no real SI/DTC → return None → BLOCK ALERT
    """
    return None  # <-- until real data source added

# =========================
# CLASSIFICATION
# =========================

def classify(structure, change_pct):
    si = structure["si"]
    dtc = structure["dtc"]

    # TIME BOMB EXTENDED
    if si >= 20 and dtc >= 5 and change_pct >= 10:
        return "TIME_BOMB_EXTENDED"

    # TIME BOMB LOADED
    if si >= 20 and dtc >= 5 and change_pct >= 5:
        return "TIME_BOMB_LOADED"

    # PRESSURE COOKER
    if si >= 15 and dtc >= 3 and change_pct >= 2:
        return "PRESSURE_COOKER"

    return None

# =========================
# MESSAGE BUILDER
# =========================

def build_message(symbol, price, change_pct, signal, structure):

    if signal == "PRESSURE_COOKER":
        return (
            f"#{symbol}\n\n"
            f"Price: ${price} • {change_pct}%\n\n"
            f"🔥 Pressure Cooker\n\n"
            f"Structure:\n"
            f"SI: {structure['si']}% • DTC: {structure['dtc']}\n"
            f"Volume: ELEVATED\n\n"
            f"State: BUILDING\n\n"
            f"READ:\n"
            f"Short pressure is actively building. Liquidity and positioning are tightening. This is where setups begin forming — attention required."
        )

    if signal == "TIME_BOMB_LOADED":
        return (
            f"#{symbol}\n\n"
            f"Price: ${price} • {change_pct}%\n\n"
            f"💣 Ticking Time Bomb\n\n"
            f"Structure:\n"
            f"SI: {structure['si']}% • DTC: {structure['dtc']}\n"
            f"Volume: EXPANDING\n\n"
            f"State: LOADED\n\n"
            f"READ:\n"
            f"Pressure conditions are fully developed. Positioning is constrained and unstable. High potential for volatility expansion."
        )

    if signal == "TIME_BOMB_EXTENDED":
        return (
            f"#{symbol}\n\n"
            f"Price: ${price} • {change_pct}%\n\n"
            f"💣 Ticking Time Bomb\n\n"
            f"Structure:\n"
            f"SI: {structure['si']}% • DTC: {structure['dtc']}\n"
            f"Volume: EXPANDING\n\n"
            f"State: EXTENDED\n\n"
            f"READ:\n"
            f"Pressure conditions are fully developed. Positioning is constrained and unstable. High potential for volatility expansion."
        )

# =========================
# MAIN LOOP
# =========================

def run():
    state = load_state()

    while True:
        for symbol in TICKERS:

            price_data = get_price_data(symbol)
            if not price_data:
                continue

            structure = get_structure(symbol)
            if not structure:
                continue  # STRICT: block if no SI/DTC

            signal = classify(structure, price_data["change_pct"])
            if not signal:
                continue

            last = state.get(symbol, {})
            last_signal = last.get("signal")
            last_time = last.get("time", 0)

            now = time.time()

            if signal == last_signal:
                continue

            if now - last_time < COOLDOWN_SECONDS:
                continue

            message = build_message(
                symbol,
                price_data["price"],
                price_data["change_pct"],
                signal,
                structure
            )

            send_alert(CHAT_ID, message)

            state[symbol] = {
                "signal": signal,
                "time": now
            }

            save_state(state)

        time.sleep(CHECK_INTERVAL)

# =========================

if __name__ == "__main__":
    run()
