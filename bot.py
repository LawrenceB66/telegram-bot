import requests
import time
import os
import json
from signal_logic import classify_signal

# =========================
# ENV VARIABLES
# =========================

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# =========================
# CONFIG
# =========================

WATCHLIST = [
    "AMC", "GME", "CVNA", "UPST"
]

CHECK_INTERVAL = 30  # seconds

STATE_FILE = "state.json"

# =========================
# STATE ENGINE (LOCKED)
# =========================

def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def should_alert(symbol, new_state):
    state = load_state()

    last_state = state.get(symbol)

    # 🚫 Block duplicate state
    if last_state == new_state:
        return False

    # ✅ Save new state
    state[symbol] = new_state
    save_state(state)

    return True

# =========================
# TELEGRAM
# =========================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=payload)

# =========================
# DATA FETCH
# =========================

def get_quote(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
    r = requests.get(url)
    data = r.json()

    price = data.get("c", 0)
    prev_close = data.get("pc", 0)

    if prev_close == 0:
        return None

    pct_change = ((price - prev_close) / prev_close) * 100

    return round(price, 2), round(pct_change, 2)

# =========================
# MAIN LOOP
# =========================

def run():
    print("IAL ENGINE LIVE")

    while True:
        for symbol in WATCHLIST:
            try:
                quote = get_quote(symbol)
                if not quote:
                    continue

                price, pct = quote

                # TEMP STRUCTURE (PLACEHOLDER)
                structure = {
                    "rvol": 2.0,
                    "velocity": "ACCELERATING"
                }

                signal = classify_signal(symbol, pct, structure)

                if signal:
                    state_name = signal["state"]

                    if should_alert(symbol, state_name):

                        message = (
                            f"{symbol}\n\n"
                            f"Price: {price} • {pct}%\n\n"
                            f"{signal['emoji']}\n\n"
                            f"Structure:\n"
                            f"Volume: {signal['volume']}\n"
                            f"Velocity: {signal['velocity']}"
                        )

                        send_telegram(message)
                        print(f"ALERT SENT: {symbol} {state_name}")

            except Exception as e:
                print(f"Error with {symbol}: {e}")

        time.sleep(CHECK_INTERVAL)

# =========================
# START
# =========================

if __name__ == "__main__":
    run()
