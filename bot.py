import requests
import time
import os

# --- SAFE REQUEST ---
def safe_request(url, params=None, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=(5, 30))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Attempt {attempt+1} failed: {e}")
            time.sleep(5)
    return None


# --- CONFIG ---
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = -1003667470993
URL = f"https://api.telegram.org/bot{TOKEN}/"


# --- ALERT SENDER ---
def send_alert(ticker, price, pct, tier, dtc, si, velocity):
    message = (
        f"${ticker}\n"
        f"Price {price} • {pct}%\n\n"
        f"{tier}\n\n"
        f"DTC: {dtc} • SI: {si}%\n"
        f"Velocity: {velocity}"
    )

    safe_request(URL + "sendMessage", {
        "chat_id": CHANNEL_ID,
        "text": message
    })


# --- MOCK DATA (TEMP ENGINE) ---
def get_mock_top5():
    return [
        {"ticker": "AMC", "price": "1.50", "pct": "-0.66", "tier": "💣 POWDER KEG", "dtc": "6.2", "si": "38", "velocity": "-0.004"},
        {"ticker": "GME", "price": "24.11", "pct": "3.43", "tier": "💣 POWDER KEG", "dtc": "3.8", "si": "21", "velocity": "-0.012"},
        {"ticker": "BBBY", "price": "0.42", "pct": "5.10", "tier": "🔥 TICKING TIME BOMB", "dtc": "1.9", "si": "47", "velocity": "0.021"},
        {"ticker": "CVNA", "price": "88.20", "pct": "2.12", "tier": "🔥 TICKING TIME BOMB", "dtc": "2.3", "si": "31", "velocity": "0.015"},
        {"ticker": "UPST", "price": "22.50", "pct": "-1.02", "tier": "💣 POWDER KEG", "dtc": "5.1", "si": "29", "velocity": "-0.008"},
    ]


# --- STATE TRACKING ENGINE ---
last_sent = {}

def should_alert(stock):
    ticker = stock["ticker"]

    # First time seeing ticker → send
    if ticker not in last_sent:
        last_sent[ticker] = stock
        return True

    prev = last_sent[ticker]

    try:
        price_changed = stock["price"] != prev["price"]
        pct_jump = abs(float(stock["pct"]) - float(prev["pct"])) >= 1.0
        velocity_shift = abs(float(stock["velocity"]) - float(prev["velocity"])) >= 0.01
    except:
        return False

    if price_changed or pct_jump or velocity_shift:
        last_sent[ticker] = stock
        return True

    return False


# --- MAIN LOOP ---
while True:
    top5 = get_mock_top5()

    for stock in top5:
        if should_alert(stock):
            send_alert(
                stock["ticker"],
                stock["price"],
                stock["pct"],
                stock["tier"],
                stock["dtc"],
                stock["si"],
                stock["velocity"]
            )
            time.sleep(1)

    time.sleep(30)
