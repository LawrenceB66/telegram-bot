import requests
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

TICKERS = ["AMC", "CVNA", "UPST"]
POLL_INTERVAL = 60

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
        "volume": data.get("v")
    }

# =========================
# % CHANGE
# =========================
def percent_change(price, prev):
    if not price or not prev:
        return 0
    return round(((price - prev) / prev) * 100, 2)

# =========================
# EVENT ENGINE (ONLY TRIGGER)
# =========================
def detect_event(change):
    if abs(change) >= 25:
        return "🚨 BREAKOUT EVENT", f"{change}% move (EXTREME)"

    if abs(change) >= 10:
        return "⚡ MOMENTUM", f"{change}% move"

    if abs(change) >= 5:
        return "🟡 EARLY MOVE", f"{change}% move"

    return None, None

# =========================
# STRUCTURE ENGINE (CONTEXT ONLY)
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

    print(f"Price: {price} | Change: {change}%")

    # =========================
    # EVENT (TRIGGER)
    # =========================
    event_label, event_reason = detect_event(change)

    # 🚫 HARD STOP — NO EVENT = NO ALERT
    if not event_label:
        print(f"❌ No event for {ticker}")
        return

    # =========================
    # STRUCTURE (CONTEXT ONLY)
    # =========================
    # TEMP placeholders (until real SI/DTC wired)
    si = 35
    dtc = 6

    struct_label, struct_reason = detect_structure(si, dtc)

    # =========================
    # BUILD MESSAGE
    # =========================
    msg = f"${ticker}\nPrice: {price}\nMove: {change}%\n\n"

    # EVENT FIRST (CAUSE)
    msg += f"{event_label}\n{event_reason}\n\n"

    # STRUCTURE SECOND (CONTEXT)
    if struct_label:
        msg += f"{struct_label}\n{struct_reason}"

    # =========================
    # SEND
    # =========================
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
