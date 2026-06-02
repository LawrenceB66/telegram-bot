import requests
import time
import os
import json

from send_alert import send_alert

# =========================
# CONFIG
# =========================

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

CHECK_INTERVAL = 30
COOLDOWN_SECONDS = 300

STATE_FILE = "state.json"
STRUCTURE_FILE = "structure.json"

# =========================
# LOAD FILES
# =========================

def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

# =========================
# DATA FETCH
# =========================

def get_price(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        r = requests.get(url, timeout=5)
        data = r.json()

        price = data.get("c")
        prev_close = data.get("pc")

        if price and prev_close:
            pct = ((price - prev_close) / prev_close) * 100
            return round(price, 2), round(pct, 2)
    except:
        pass

    return None, None

# =========================
# STRUCTURE CHECK
# =========================

def get_structure(symbol, structure_data):
    return structure_data.get(symbol)

# =========================
# SIGNAL LOGIC (STRICT IAL)
# =========================

def classify_signal(symbol, price, pct, structure):

    si = structure["si"]
    dtc = structure["dtc"]

    # 💣 TIME BOMB EXTENDED
    if si >= 20 and dtc >= 5 and pct >= 10:
        return {
            "emoji": "💣",
            "name": "Ticking Time Bomb",
            "state": "EXTENDED",
            "volume": "EXPANDING",
            "read": "Pressure conditions are fully developed. Positioning is constrained and unstable. High potential for volatility expansion."
        }

    # 💣 TIME BOMB LOADED
    if si >= 20 and dtc >= 5 and pct >= 5:
        return {
            "emoji": "💣",
            "name": "Ticking Time Bomb",
            "state": "LOADED",
            "volume": "EXPANDING",
            "read": "Pressure conditions are fully developed. Positioning is constrained and unstable. High potential for volatility expansion."
        }

    # 🔥 PRESSURE COOKER
    if si >= 15 and dtc >= 3 and pct >= 2:
        return {
            "emoji": "🔥",
            "name": "Pressure Cooker",
            "state": "BUILDING",
            "volume": "ELEVATED",
            "read": "Short pressure is actively building. Liquidity and positioning are tightening. This is where setups begin forming — attention required."
        }

    return None

# =========================
# MESSAGE FORMAT (LOCKED)
# =========================

def build_message(symbol, price, pct, signal, structure):

    return (
        f"#{symbol}\n\n"
        f"Price: ${price:.2f} • {pct:.2f}%\n\n"
        f"{signal['emoji']} {signal['name']}\n\n"
        f"Structure:\n"
        f"SI: {structure['si']}% • DTC: {structure['dtc']}\n"
        f"Volume: {signal['volume']}\n\n"
        f"State: {signal['state']}\n\n"
        f"READ:\n"
        f"{signal['read']}"
    )

# =========================
# MAIN ENGINE
# =========================

def run():
    print("IAL STRUCTURE ENGINE ACTIVE")

    state_data = load_json(STATE_FILE)
    structure_data = load_json(STRUCTURE_FILE)

    while True:
        now = time.time()

        for symbol in structure_data.keys():

            price, pct = get_price(symbol)

            if price is None:
                continue

            structure = get_structure(symbol, structure_data)

            if not structure:
                continue  # 🔒 NO STRUCTURE = NO SIGNAL

            signal = classify_signal(symbol, price, pct, structure)

            if not signal:
                continue  # 🔒 BELOW THRESHOLD = SILENCE

            prev = state_data.get(symbol, {})
            prev_state = prev.get("state")
            last_alert = prev.get("last_alert", 0)

            # 🔒 STATE CHANGE ONLY
            if signal["state"] == prev_state:
                continue

            # 🔒 COOLDOWN
            if now - last_alert < COOLDOWN_SECONDS:
                continue

            message = build_message(symbol, price, pct, signal, structure)

            send_alert(message)
            print(f"ALERT: {symbol} → {signal['state']}")

            state_data[symbol] = {
                "state": signal["state"],
                "last_alert": now
            }

            time.sleep(1)

        save_json(STATE_FILE, state_data)

        print("Cycle complete. Waiting...")
        time.sleep(CHECK_INTERVAL)

# =========================
# START
# =========================

if __name__ == "__main__":
    run()
