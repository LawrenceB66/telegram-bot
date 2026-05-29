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
# STATE TRACKING
# =========================
STATE_CACHE = {}

# =========================
# COOLDOWN
# =========================
LAST_ALERT_TIME = {}
COOLDOWN_SECONDS = 1800  # 30 minutes

# =========================
# SHORT INTEREST CACHE (TEMP)
# Replace with real data later
# =========================
SI_CACHE = {
    "AMC": 25.0,
    "GME": 22.0,
    "CVNA": 18.0,
    "UPST": 20.0,
    "SOFI": 12.0,
    "LCID": 15.0,
    "RIVN": 10.0,
    "SHOP": 8.0,
    "PINS": 9.0,
    "ROKU": 11.0,
    "FUBO": 30.0,
    "DKNG": 14.0,
    "RUN": 13.0,
    "ENPH": 7.0,
    "NIO": 6.0
}

# =========================
# STATIC READ TEXT
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

def get_price_volume(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
    data = safe_request(url)

    if not data or "c" not in data:
        return None, None, None

    price = data["c"]
    prev = data["pc"]

    if not price or not prev:
        return None, None, None

    pct = ((price - prev) / prev) * 100

    # Volume proxy using % movement
    if abs(pct) >= 5:
        volume = 2.0
    elif abs(pct) >= 3:
        volume = 1.5
    else:
        volume = 1.0

    return round(price, 2), round(pct, 2), volume

# =========================
# DTC CALCULATION
# =========================
def calculate_dtc(si, volume_factor):
    if volume_factor == 0:
        return 0
    return round(si / volume_factor, 2)

# =========================
# CORE ENGINE
# =========================
def evaluate_signal(symbol):

    price, pct, volume_factor = get_price_volume(symbol)
    if price is None:
        return

    si = SI_CACHE.get(symbol, 0)

    # Calculate DTC dynamically
    dtc = calculate_dtc(si, volume_factor)

    # HARD FILTERS
    if si < 15:
        return

    if abs(pct) < 3:
        return

    state = None
    signal_name = ""
    emoji = ""
    read = ""

    # SIGNAL LOGIC
    if si >= 20 and dtc >= 5 and pct >= 5:
        state = "LOADED"
        signal_name = "Ticking Time Bomb"
        emoji = "💣"
        read = READ_TIME_BOMB

    elif si >= 15 and dtc >= 3 and pct >= 3:
        state = "BUILDING"
        signal_name = "Pressure Cooker"
        emoji = "🔥"
        read = READ_PRESSURE_COOKER

    else:
        return

    prev_state = STATE_CACHE.get(symbol)

    if prev_state == state:
        return

    # COOLDOWN
    now = time.time()
    last_time = LAST_ALERT_TIME.get(symbol, 0)

    if now - last_time < COOLDOWN_SECONDS:
        print(f"COOLDOWN: {symbol}")
        return

    LAST_ALERT_TIME[symbol] = now
    STATE_CACHE[symbol] = state

    # MESSAGE
    message = f"""{symbol}

Price: {price} • {pct}%

{emoji} {signal_name}

Structure:
SI: {si}% • DTC: {dtc}

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
    try:
        requests.post(TG_URL, data={
            "chat_id": CHAT_ID,
            "text": msg
        })
    except Exception as e:
        print("Telegram error:", e)

# =========================
# LOOP
# =========================
def run():
    print("BOT STARTED")

    while True:
        for symbol in WATCHLIST:
            evaluate_signal(symbol)
            time.sleep(1)

        time.sleep(20)

if __name__ == "__main__":
    run()
