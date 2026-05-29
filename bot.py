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

def get_price_data(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
    data = safe_request(url)

    if not data or "c" not in data:
        return None, None

    price = data["c"]
    prev = data["pc"]

    if not price or not prev:
        return None, None

    pct = ((price - prev) / prev) * 100
    return round(price, 2), round(pct, 2)

# =========================
# VOLUME PROXY
# =========================
def get_volume_label(pct):
    if abs(pct) >= 5:
        return "EXPANDING"
    elif abs(pct) >= 3:
        return "ELEVATED"
    return "NORMAL"

# =========================
# CORE ENGINE (NO SI/DTC)
# =========================
def evaluate_signal(symbol):

    price, pct = get_price_data(symbol)
    if price is None:
        return

    # 🔥 HARD FILTER 1 — movement
    if abs(pct) < 3:
        return

    volume = get_volume_label(pct)

    state = None
    signal_name = ""
    emoji = ""
    read = ""

    # 🔥 STRONG SIGNALS ONLY
    if pct >= 5:
        state = "LOADED"
        signal_name = "Ticking Time Bomb"
        emoji = "💣"
        read = READ_TIME_BOMB
        volume = "EXPANDING"

    elif pct >= 3:
        state = "BUILDING"
        signal_name = "Pressure Cooker"
        emoji = "🔥"
        read = READ_PRESSURE_COOKER

    else:
        return

    prev_state = STATE_CACHE.get(symbol)

    if prev_state == state:
        return

    # =========================
    # COOLDOWN
    # =========================
    now = time.time()
    last_time = LAST_ALERT_TIME.get(symbol, 0)

    if now - last_time < COOLDOWN_SECONDS:
        print(f"COOLDOWN: {symbol}")
        return

    LAST_ALERT_TIME[symbol] = now
    STATE_CACHE[symbol] = state

    # =========================
    # MESSAGE (CLEAN FORMAT)
    # =========================
    message = f"""{symbol}

Price: {price} • {pct}%

{emoji} {signal_name}

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
