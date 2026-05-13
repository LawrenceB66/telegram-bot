import os
import time
import requests

# =========================
# ENV VARIABLES
# =========================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# =========================
# CONFIG
# =========================
TICKERS = ["AMC", "CVNA", "UPST"]
POLL_INTERVAL = 60

# =========================
# STATE MEMORY (PERSIST DURING RUNTIME)
# =========================
last_signal = {}
last_state = {}
last_alert_time = {}

COOLDOWN_SECONDS = 900  # 15 min safety lock

# =========================
# SAFE REQUEST
# =========================
def safe_request(url):
    try:
        response = requests.get(url, timeout=10)
        return response.json()
    except Exception as e:
        print(f"❌ Request error: {e}")
        return None

# =========================
# PRICE + CHANGE
# =========================
def get_price_data(ticker):
    url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_API_KEY}"
    data = safe_request(url)

    if not data or "c" not in data:
        print(f"⚠️ No price data for {ticker}")
        return None, None

    price = data.get("c")
    prev = data.get("pc")

    if price and prev:
        change = ((price - prev) / prev) * 100
    else:
        change = 0

    return round(price, 2), round(change, 2)

# =========================
# MOCK STRUCTURE (REPLACE LATER)
# =========================
def get_structure_data(ticker):
    mock = {
        "AMC": (42, 9),
        "CVNA": (28, 4),
        "UPST": (35, 6)
    }
    return mock.get(ticker, (0, 0))

# =========================
# VOLUME (TEMP LOGIC)
# =========================
def get_volume_status(change):
    if abs(change) >= 15:
        return "SURGING"
    elif abs(change) >= 7:
        return "ELEVATED"
    return "NORMAL"

# =========================
# EVENT DETECTION (STRICT)
# =========================
def detect_event(change, volume):
    if abs(change) >= 15 and volume in ["SURGING", "ELEVATED"]:
        return True
    return False

# =========================
# STRUCTURE CLASSIFICATION
# =========================
def classify_structure(si, dtc):
    if si >= 40 and dtc >= 8:
        return "TTB", "ESCALATION"

    elif si >= 30 and dtc >= 5:
        return "PRESSURE", "BUILDING"

    elif si >= 20 and dtc >= 3:
        return "BASE", "LOADED"

    return None, None

# =========================
# ALERT FILTER (ANTI-SPAM CORE)
# =========================
def should_alert(ticker, signal, state):
    prev_signal = last_signal.get(ticker)
    prev_state = last_state.get(ticker)

    # First time = allow
    if prev_signal is None:
        print(f"🆕 First signal for {ticker}")
        return True

    # No change = block
    if signal == prev_signal and state == prev_state:
        print(f"⏭️ No change for {ticker}")
        return False

    # Cooldown protection
    now = time.time()
    last_time = last_alert_time.get(ticker, 0)

    if now - last_time < COOLDOWN_SECONDS:
        print(f"⏳ Cooldown active for {ticker}")
        return False

    return True

# =========================
# FORMAT MESSAGE
# =========================
def format_alert(ticker, price, change, signal, si, dtc, volume, state):
    icons = {
        "TTB": "💣",
        "PRESSURE": "🔥",
        "BASE": "🧱",
        "EVENT": "🚨"
    }

    names = {
        "TTB": "Ticking Time Bomb",
        "PRESSURE": "Pressure Cooker",
        "BASE": "Baseline",
        "EVENT": "Breakout Event"
    }

    message = f"""
${ticker}
Price: {price} • {change}%

{icons[signal]} {names[signal]}

Structure:
SI: {si}%
DTC: {dtc}
Volume: {volume}

State: {state}
"""

    return message.strip()

# =========================
# SEND TELEGRAM
# =========================
def send_alert(message):
    try:
        requests.post(BASE_URL, json={
            "chat_id": CHAT_ID,
            "text": message
        })
    except Exception as e:
        print(f"❌ Telegram error: {e}")

# =========================
# PROCESS ENGINE
# =========================
def process_ticker(ticker):
    print(f"🔎 Processing {ticker}")

    price, change = get_price_data(ticker)
    if price is None:
        return

    si, dtc = get_structure_data(ticker)
    volume = get_volume_status(change)

    # PRIORITY: EVENT ENGINE
    if detect_event(change, volume):
        signal = "EVENT"
        state = "ACTIVE"

    else:
        signal, state = classify_structure(si, dtc)

    if signal is None:
        print(f"❌ No valid structure for {ticker}")
        return

    # FILTER
    if not should_alert(ticker, signal, state):
        return

    # SEND
    message = format_alert(ticker, price, change, signal, si, dtc, volume, state)

    print(f"📡 ALERT: {ticker} → {signal} ({state})")
    send_alert(message)

    # UPDATE MEMORY
    last_signal[ticker] = signal
    last_state[ticker] = state
    last_alert_time[ticker] = time.time()

# =========================
# MAIN LOOP
# =========================
def run():
    while True:
        print("\n🔄 New cycle...\n")

        for ticker in TICKERS:
            process_ticker(ticker)

        print("😴 Sleeping...\n")
        time.sleep(POLL_INTERVAL)

# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    print("🚀 STRUCTURED EQUITY PRESSURE ENGINE LIVE")
    run()
