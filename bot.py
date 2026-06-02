import requests
import time
import os
import json

from send_alert import send_alert

# ============================
# CONFIG
# ============================

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

CHECK_INTERVAL = 30
COOLDOWN_SECONDS = 300

STATE_FILE = "state.json"

TICKERS = [
    "AMC","GME","CVNA","UPST","LCID","RIVN","NIO","XPEV",
    "PLTR","AI","SOFI","HOOD","AFRM","DKNG","OPEN","QS",
    "TLRY","FUBO","NKLA","FFIE","MULN","MARA","RIOT","COIN",
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","DIS",
    "BABA","UBER","LYFT","SQ","PYPL","JPM","BAC","WFC",
    "C","GS","MS"
]

# ============================
# STATE HANDLING
# ============================

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# ============================
# MARKET DATA
# ============================

def get_price(ticker):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_API_KEY}"
        r = requests.get(url, timeout=5)
        data = r.json()
        return data.get("c", 0)
    except:
        return 0

# ============================
# STATE ENGINE LOGIC
# ============================

def get_state(price, prev_price):
    if prev_price == 0:
        return "BASELINE"

    change_pct = ((price - prev_price) / prev_price) * 100

    if abs(change_pct) < 1:
        return "BASELINE"
    elif abs(change_pct) < 3:
        return "BUILDING"
    elif abs(change_pct) < 6:
        return "LOADED"
    else:
        return "EXTENDED"

# ============================
# MAIN LOOP
# ============================

def run():
    print("🚀 STATE ENGINE ACTIVE")

    state = load_state()

    while True:
        for ticker in TICKERS:

            price = get_price(ticker)

            if ticker not in state:
                state[ticker] = {
                    "last_price": price,
                    "state": "BASELINE",
                    "last_alert": 0
                }
                continue

            prev_price = state[ticker]["last_price"]
            prev_state = state[ticker]["state"]
            last_alert = state[ticker]["last_alert"]

            current_state = get_state(price, prev_price)

            # ONLY act on state change
            if current_state != prev_state:

                now = time.time()

                # cooldown protection
                if now - last_alert > COOLDOWN_SECONDS:

                    message = f"{ticker} → {current_state}"

                    send_alert(message)

                    state[ticker]["last_alert"] = now

                    print(f"✅ {ticker} moved {prev_state} → {current_state}")

            # update tracking
            state[ticker]["last_price"] = price
            state[ticker]["state"] = current_state

        save_state(state)

        print("🧠 State cycle complete. Waiting...")
        time.sleep(CHECK_INTERVAL)


# ============================
# START
# ============================

if __name__ == "__main__":
    run()
