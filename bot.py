import requests
import time
import os
from collections import defaultdict, deque

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

TICKERS = ["AMC", "CVNA", "UPST"]
POLL_INTERVAL = 60

# =========================
# VOLUME TRACKING
# =========================
volume_history = defaultdict(lambda: deque(maxlen=20))  # last 20 cycles

# =========================
# SAFE REQUEST
# =========================
def safe_request(url):
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"⚠️ Request failed: {e}")
    return None

# =========================
# GET QUOTE
# =========================
def get_quote(ticker):
    url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_API_KEY}"
    data = safe_request(url)

    if not data:
        print(f"⚠️ No data for {ticker}")
        return None

    return {
        "price": data.get("c"),
        "prev": data.get("pc"),
        "volume": data.get("v") or 0
    }

# =========================
# % CHANGE
# =========================
def percent_change(price, prev):
    if not price or not prev:
        return 0
    return round(((price - prev) / prev) * 100, 2)

# =========================
# VOLUME MULTIPLIER
# =========================
def get_volume_multiplier(ticker, current_volume):
    history = volume_history[ticker]

    # store volume
    history.append(current_volume)

    if len(history) < 5:
        return 0  # not enough data yet

    avg_volume = sum(history) / len(history)

    if avg_volume == 0:
        return 0

    return round(current_volume / avg_volume, 2)

# =========================
# EVENT ENGINE (CONSERVATIVE)
# =========================
def detect_event(change, vol_mult):
    if vol_mult == 0:
        return None, None

    # 🚨 BREAKOUT
    if abs(change) >= 20 and vol_mult >= 5:
        return "🚨 BREAKOUT", f"{change}% move | Vol {vol_mult}x"

    # ⚡ MOMENTUM
    if abs(change) >= 12 and vol_mult >= 4:
        return "⚡ MOMENTUM", f"{change}% move | Vol {vol_mult}x"

    # 🟡 EARLY MOVE
    if abs(change) >= 7 and vol_mult >= 3:
        return "🟡 EARLY MOVE", f"{change}% move | Vol {vol_mult}x"

    return None, None

# =========================
# STRUCTURE (CONTEXT ONLY)
# =========================
def detect_structure(si, dtc):
    if si >= 40 and dtc >= 8:
        return "💣 TICKING TIME BOMB", f"SI {si}% | DTC {dtc}"

    if si >= 30 and dtc >= 5:
        return "🔥 PRESSURE COOKER", f"SI {si}% | DTC {dtc}"

    if si >= 20 and dtc >= 3:
        return "🧱 BASELINE", f"SI {si}% | DTC {dtc}"

    return None, None

# =========================
# SEND ALERT
# =========================
def send_alert(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg})

# =========================
# PROCESS
# =========================
def process_ticker(ticker):
    print(f"🔎 Processing {ticker}")

    data = get_quote(ticker)
    if not data:
        return

    price = data["price"]
    prev = data["prev"]
    volume = data["volume"]

    change = percent_change(price, prev)
    vol_mult = get_volume_multiplier(ticker, volume)

    print(f"Price: {price} | Change: {change}% | Vol: {vol_mult}x")

    # =========================
    # EVENT (TRIGGER)
    # =========================
    event_label, event_reason = detect_event(change, vol_mult)

    if not event_label:
        print(f"❌ No event for {ticker}")
        return

    # =========================
    # STRUCTURE (TEMP)
    # =========================
    si = 35
    dtc = 6

    struct_label, struct_reason = detect_structure(si, dtc)

    # =========================
    # MESSAGE
    # =========================
    msg = f"${ticker}\nPrice: {price}\nMove: {change}%\n\n"

    msg += f"{event_label}\n{event_reason}\n\n"

    if struct_label:
        msg += f"{struct_label}\n{struct_reason}"

    print(f"📤 Sending alert for {ticker}")
    send_alert(msg)

# =========================
# MAIN LOOP
# =========================
def run():
    print("🚀 Bot started...")

    while True:
        print("\n🔁 New cycle...\n")

        for ticker in TICKERS:
            process_ticker(ticker)

        print("😴 Sleeping...\n")
        time.sleep(POLL_INTERVAL)

# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    run()
