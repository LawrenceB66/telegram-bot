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
# STATE MEMORY
# =========================
last_signal = {}
last_state = {}

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
# GET PRICE DATA
# =========================
def get_price_data(ticker):
    url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_API_KEY}"
    data = safe_request(url)

    if not data or "c" not in data:
        print(f"⚠️ No data for {ticker}")
        return None, None

    price = data.get("c")
    prev = data.get("pc")

    if price and prev:
        change = ((price - prev) / prev) * 100
    else:
        change = 0

    return round(price, 2), round(change, 2)

# =========================
# MOCK STRUCTURE (ANCHOR)
# =========================
def get_structure_data(ticker):
    mock_data = {
        "AMC": (42, 9),
        "CVNA": (28, 4),
        "UPST": (35, 6)
    }
    return mock_data.get(ticker, (0, 0))

# =========================
# VOLUME (PLACEHOLDER)
# =========================
def get_volume_status():
    return "ELEVATED"

# =========================
# EVENT ENGINE (LOCKED)
# =========================
def detect_event(change):
    abs_change = abs(change)

    if abs_change >= 20:
        return "EXTREME", "EVENT"
    elif abs_change >= 12:
        return "STRONG", "EVENT"
    elif abs_change >= 8:
        return "BREAKOUT", "EVENT"

    return None, None

# =========================
# STRUCTURE ENGINE
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
# FORMAT ALERT
# =========================
def format_alert(ticker, price, change, signal, si, dtc, volume, state):
    icons = {
        "TTB": "💣",
        "PRESSURE": "🔥",
        "BASE": "🧱",
        "BREAKOUT": "🚨",
        "STRONG": "⚡",
        "EXTREME": "🧨"
    }

    names = {
        "TTB": "Ticking Time Bomb",
        "PRESSURE": "Pressure Cooker",
        "BASE": "Baseline",
        "BREAKOUT": "Breakout Move",
        "STRONG": "Strong Move",
        "EXTREME": "Extreme Move"
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
# SEND ALERT
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
# PROCESS TICKER
# =========================
def process_ticker(ticker):
    print(f"🔎 Processing {ticker}")

    price, change = get_price_data(ticker)
    if price is None:
        return

    si, dtc = get_structure_data(ticker)
    volume = get_volume_status()

    # =========================
    # PRIORITY: EVENT ENGINE
    # =========================
    signal, state = detect_event(change)

    # =========================
    # FALLBACK: STRUCTURE
    # =========================
    if signal is None:
        signal, state = classify_structure(si, dtc)

    # NO SIGNAL → NO ALERT
    if signal is None:
        print(f"❌ No valid signal for {ticker}")
        return

    # =========================
    # STATE MEMORY FILTER
    # =========================
    prev_signal = last_signal.get(ticker)
    prev_state = last_state.get(ticker)

    if signal == prev_signal and state == prev_state:
        print(f"⏭️ No change for {ticker}")
        return

    # =========================
    # SEND ALERT
    # =========================
    message = format_alert(ticker, price, change, signal, si, dtc, volume, state)

    print(f"📡 ALERT: {ticker} → {signal} ({state})")
    send_alert(message)

    # =========================
    # UPDATE MEMORY
    # =========================
    last_signal[ticker] = signal
    last_state[ticker] = state

# =========================
# MAIN LOOP
# =========================
def run():
    print("🚀 STRUCTURED EQUITY PRESSURE ENGINE LIVE\n")

    while True:
        print("\n🔄 New cycle...\n")

        for ticker in TICKERS:
            process_ticker(ticker)

        print("😴 Sleeping...\n")
        time.sleep(POLL_INTERVAL)

# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    run()
