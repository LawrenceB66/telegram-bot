import os
import time
import requests

# =========================
# ENV
# =========================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

TICKERS = ["AMC", "CVNA", "UPST"]
POLL_INTERVAL = 60

# =========================
# MEMORY
# =========================
last_alert_time = {}
last_velocity = {}

# =========================
# CONFIG
# =========================
VELOCITY_THRESHOLD = 5
VOLUME_MULTIPLIER = 2
COOLDOWN = 180  # 3 min

SI_PRESSURE = 30
SI_BOMB = 40

# =========================
# UTIL
# =========================
def safe_request(url):
    try:
        return requests.get(url, timeout=10).json()
    except:
        return None

def should_alert(ticker):
    now = time.time()
    if ticker not in last_alert_time:
        last_alert_time[ticker] = now
        return True

    if now - last_alert_time[ticker] > COOLDOWN:
        last_alert_time[ticker] = now
        return True

    return False

# =========================
# DATA
# =========================
def get_price_data(ticker):
    url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_API_KEY}"
    data = safe_request(url)

    if not data:
        return None

    price = data.get("c")
    prev = data.get("pc")

    if not price or not prev:
        return None

    change = ((price - prev) / prev) * 100

    return {
        "price": round(price, 2),
        "change_pct": round(change, 2),
        "volume": data.get("v", 0),
        "avg_volume": data.get("v", 0)  # placeholder until upgraded
    }

# =========================
# MOCK STRUCTURE (TEMP)
# =========================
def get_structure_data(ticker):
    mock = {
        "AMC": (42, 9),
        "CVNA": (28, 4),
        "UPST": (35, 6)
    }
    si, dtc = mock.get(ticker, (0, 0))

    return {
        "si": si,
        "dtc": dtc
    }

# =========================
# DETECT VELOCITY
# =========================
def detect_velocity(data, ticker):
    change = data["change_pct"]
    volume = data["volume"]
    avg_volume = data["avg_volume"]

    if volume < VOLUME_MULTIPLIER * avg_volume:
        return None

    if change >= VELOCITY_THRESHOLD:
        return "⚡ BULL VELOCITY"

    elif change <= -VELOCITY_THRESHOLD:
        return "🩸 BEAR VELOCITY"

    return None

# =========================
# DETECT PRESSURE
# =========================
def detect_pressure(struct):
    si = struct["si"]

    if si >= SI_BOMB:
        return "💣 TIME BOMB"

    elif si >= SI_PRESSURE:
        return "🔥 PRESSURE"

    return None

# =========================
# FORMAT
# =========================
def format_alert(ticker, data, struct, tag):
    return f"""
${ticker}
Price {data['price']} • {data['change_pct']}%

{tag}

DTC: {struct['dtc']} • SI: {struct['si']}%
""".strip()

# =========================
# SEND
# =========================
def send_alert(message):
    try:
        requests.post(BASE_URL, json={
            "chat_id": CHAT_ID,
            "text": message
        })
    except:
        pass

# =========================
# ENGINE
# =========================
def process_ticker(ticker):

    data = get_price_data(ticker)
    if not data:
        return

    struct = get_structure_data(ticker)

    velocity = detect_velocity(data, ticker)
    pressure = detect_pressure(struct)

    # ⚡ VELOCITY (ALWAYS PUSH)
    if velocity and should_alert(ticker):
        send_alert(format_alert(ticker, data, struct, velocity))

    # 🔥 PRESSURE
    if pressure and should_alert(ticker):
        send_alert(format_alert(ticker, data, struct, pressure))

    # 💣⚡ / 💣🩸 CONVERGENCE
    if velocity and pressure and should_alert(ticker):
        if "BULL" in velocity:
            tag = "💣⚡ CONVERGENCE"
        else:
            tag = "💣🩸 CONVERGENCE"

        send_alert(format_alert(ticker, data, struct, tag))

    # ⚠️ REVERSAL DETECTION
    prev = last_velocity.get(ticker)

    if prev and velocity and prev != velocity:
        send_alert(format_alert(ticker, data, struct, "⚠️ REVERSAL"))

    if velocity:
        last_velocity[ticker] = velocity

# =========================
# LOOP
# =========================
def run():
    while True:
        for ticker in TICKERS:
            process_ticker(ticker)

        time.sleep(POLL_INTERVAL)

# =========================
# START
# =========================
if __name__ == "__main__":
    print("🚀 IAL ENGINE LIVE")
    run()
