print("FILE LOADED")

import os
import time
import requests

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

TG_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

WATCHLIST = [
    "AMC","GME","CVNA","UPST","SOFI","LCID","RIVN","SHOP",
    "PINS","ROKU","FUBO","DKNG","RUN","ENPH","NIO"
]

# =========================
# STATE TRACKING (CRITICAL)
# =========================
STATE_CACHE = {}
LAST_ALERT_TIME = {}

COOLDOWN_SECONDS = 900  # 15 min

# =========================
# STATIC READ TEXT (LOCKED)
# =========================
READ_PRESSURE_COOKER = "Short pressure is building. Liquidity and positioning are tightening."
READ_TIME_BOMB = "Pressure is fully developed. Positioning is constrained. Expansion risk elevated."

# =========================
# HELPERS
# =========================
def safe_request(url):
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except:
        return None

def get_price(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
    data = safe_request(url)

    if not data or "c" not in data:
        return None, None

    price = data["c"]
    prev = data["pc"]

    if not price or not prev:
        return None, None

    pct = ((price - prev) / prev) * 100
    return price, pct

# =========================
# ⚠️ PLACEHOLDER STRUCTURE
# =========================
def get_structure(symbol):
    import random
    SI = random.uniform(10, 30)
    DTC = random.uniform(2, 7)
    return round(SI, 2), round(DTC, 2)

def get_volume_label(pct):
    if pct >= 5:
        return "EXPANDING"
    elif pct >= 2:
        return "ELEVATED"
    return "NORMAL"

# =========================
# COOLDOWN CONTROL
# =========================
def cooldown_passed(symbol):
    now = time.time()

    if symbol not in LAST_ALERT_TIME:
        LAST_ALERT_TIME[symbol] = now
        return True

    if now - LAST_ALERT_TIME[symbol] >= COOLDOWN_SECONDS:
        LAST_ALERT_TIME[symbol] = now
        return True

    return False

# =========================
# CORE ENGINE
# =========================
def evaluate_signal(symbol):

    price, pct = get_price(symbol)
    if price is None:
        print(f"SKIP: {symbol} — No price data")
        return

    SI, DTC = get_structure(symbol)

    # =========================
    # STRUCTURE FILTER (HARD RULE)
    # =========================
    if SI < 15 or DTC < 3:
        STATE_CACHE[symbol] = "BASELINE"
        print(f"SKIP: {symbol} — Structure not met")
        return

    state = "BASELINE"
    signal_name = ""
    emoji = ""
    read = ""
    volume = get_volume_label(pct)

    # =========================
    # STATE LOGIC (UNCHANGED CORE)
    # =========================
    if SI >= 20 and DTC >= 5 and pct >= 5:
        state = "LOADED"
        signal_name = "Ticking Time Bomb"
        emoji = "💣"
        read = READ_TIME_BOMB
        volume = "EXPANDING"

    elif SI >= 15 and DTC >= 3 and pct >= 2:
        state = "BUILDING"
        signal_name = "Pressure Cooker"
        emoji = "🔥"
        read = READ_PRESSURE_COOKER

    else:
        state = "BASELINE"

    # =========================
    # STATE CHANGE FILTER
    # =========================
    prev_state = STATE_CACHE.get(symbol)

    if state == "BASELINE":
        STATE_CACHE[symbol] = state
        return

    if prev_state == state:
        return  # 🔒 NO DUPLICATE ALERTS

    # =========================
    # COOLDOWN FILTER (NEW)
    # =========================
    if not cooldown_passed(symbol):
        print(f"COOLDOWN: {symbol}")
        return

    STATE_CACHE[symbol] = state

    # =========================
    # FORMAT MESSAGE (LOCKED)
    # =========================
    dtc_clean = int(round(DTC))  # 🔥 FIX: NO PARTIAL DAYS

    message = f"""{symbol}

Price: {price:.2f} • {pct:.2f}%

{emoji} {signal_name}

Structure:
SI: {SI}% • DTC: {dtc_clean}
Volume: {volume}

State: {state}

READ:
{read}
"""

    send_telegram(message)
    print(f"ALERT: {symbol} → {state}")

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    requests.post(TG_URL, data={
        "chat_id": CHAT_ID,
        "text": msg
    })

# =========================
# LOOP
# =========================
def run():
    print("BOT STARTED")

    while True:
        for symbol in WATCHLIST:
            evaluate_signal(symbol)
            time.sleep(1)

        time.sleep(15)

if __name__ == "__main__":
    run()
