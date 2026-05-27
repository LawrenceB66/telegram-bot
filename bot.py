print("FILE LOADED")

import os
import time
import requests

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

TG_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

WATCHLIST = [
    "AMC","GME","CVNA","UPST",
    "RUN","ENPH","NIO","SOFI",
    "PLTR","COIN","RIVN","LCID"
]

# =========================
# MOCK STRUCTURE DATA (REPLACE LATER WITH REAL SI/DTC SOURCE)
# =========================
STRUCTURE_DATA = {
    "RUN": {"si": 22, "dtc": 5.5},
    "ENPH": {"si": 21, "dtc": 5.2},
    "NIO": {"si": 24, "dtc": 6.1},
    "SOFI": {"si": 18, "dtc": 3.5},
    "PLTR": {"si": 16, "dtc": 3.2},
    "COIN": {"si": 19, "dtc": 4.0},
    "RIVN": {"si": 23, "dtc": 5.8},
    "LCID": {"si": 25, "dtc": 6.5},
}

# =========================
# STATE TRACKING
# =========================
last_state = {}

# =========================
# HELPERS
# =========================
def get_price(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
    try:
        res = requests.get(url).json()
        return res.get("c"), res.get("dp")
    except:
        return None, None

def send_telegram(message):
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        requests.post(TG_URL, data=payload)
    except:
        pass

def format_price(price):
    return f"{price:.2f}"

def format_pct(pct):
    return f"{pct:.2f}"

# =========================
# SIGNAL ENGINE
# =========================
def evaluate_signal(symbol, price, pct, si, dtc):

    # ===== PRIORITY: TIME BOMB =====
    if si >= 20 and dtc >= 5:

        if pct >= 10:
            return {
                "signal": "💣 Ticking Time Bomb",
                "state": "EXTENDED",
                "volume": "EXPANDING",
                "read": "Pressure conditions are fully developed. Positioning is constrained and unstable. High potential for volatility expansion."
            }

        elif pct >= 5:
            return {
                "signal": "💣 Ticking Time Bomb",
                "state": "LOADED",
                "volume": "EXPANDING",
                "read": "Pressure conditions are fully developed. Positioning is constrained and unstable. High potential for volatility expansion."
            }

    # ===== PRESSURE COOKER =====
    if si >= 15 and dtc >= 3 and pct >= 2:
        return {
            "signal": "🔥 Pressure Cooker",
            "state": "BUILDING",
            "volume": "ELEVATED",
            "read": "Short pressure is actively building. Liquidity and positioning are tightening. This is where setups begin forming — attention required."
        }

    return None

# =========================
# MESSAGE BUILDER (LOCKED FORMAT)
# =========================
def build_message(symbol, price, pct, signal_data, si, dtc):

    return f"""{symbol}

Price: {format_price(price)} • {format_pct(pct)}%

{signal_data['signal']}

Structure:
SI: {si}% • DTC: {dtc}
Volume: {signal_data['volume']}

State: {signal_data['state']}

READ:
{signal_data['read']}
"""

# =========================
# MAIN LOOP
# =========================
def run():
    print("BOT STARTED")

    while True:
        for symbol in WATCHLIST:

            price, pct = get_price(symbol)

            if price is None or pct is None:
                print(f"SKIP: {symbol} - No price data")
                continue

            structure = STRUCTURE_DATA.get(symbol)

            if not structure:
                print(f"SKIP: {symbol} - No structure data")
                continue

            si = structure["si"]
            dtc = structure["dtc"]

            signal = evaluate_signal(symbol, price, pct, si, dtc)

            if not signal:
                continue

            prev = last_state.get(symbol)

            if prev == signal["state"]:
                continue  # NO REPEAT ALERTS

            last_state[symbol] = signal["state"]

            message = build_message(symbol, price, pct, signal, si, dtc)

            print(f"ALERT: {symbol} -> {signal['state']}")

            send_telegram(message)

        time.sleep(60)

# =========================
# START
# =========================
if __name__ == "__main__":
    run()
