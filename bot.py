import requests
import time
import os
import json

from send_alert import send_alert

# =========================
# CONFIG
# =========================

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

# =========================
# STATE MANAGEMENT
# =========================

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# =========================
# MAIN ENGINE
# =========================

def run():
    print("RUNNING CONTROLLED ENGINE")

    state = load_state()

    while True:
        now = time.time()

        for ticker in TICKERS:

            # initialize if missing
            if ticker not in state:
                state[ticker] = 0

            last_sent = state[ticker]

            # cooldown enforcement
            if now - last_sent < COOLDOWN_SECONDS:
                continue

            # TEST MESSAGE (safe mode)
            message = f"TEST #{ticker}"

            print(f"Sending: {ticker}")
            send_alert(message)

            # update + persist immediately
            state[ticker] = now
            save_state(state)

            # small delay prevents burst spam
            time.sleep(1)

        print("Cycle complete. Waiting...")
        time.sleep(CHECK_INTERVAL)

# =========================
# START
# =========================

if __name__ == "__main__":
    run()
