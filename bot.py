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
# LOAD / SAVE STATE
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
# FETCH DATA
# =========================

def get_quote(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        return data
    except:
        return None

# =========================
# SIGNAL LOGIC (TEMP BASELINE)
# =========================

def classify_signal(pct_change):
    if pct_change >= 5:
        return "🚀 BREAKOUT"
    elif pct_change >= 3:
        return "🔥 BUILDING"
    else:
        return None

# =========================
# MAIN LOOP
# =========================

def run():
    print("🚀 Scanner running...")

    state = load_state()

    while True:
        for ticker in TICKERS:
            data = get_quote(ticker)

            if not data:
                continue

            price = data.get("c", 0)
            prev_close = data.get("pc", 0)

            if prev_close == 0:
                continue

            pct_change = ((price - prev_close) / prev_close) * 100

            signal = classify_signal(pct_change)

            if not signal:
                continue

            last_sent = state.get(ticker, 0)
            now = time.time()

            if now - last_sent < COOLDOWN_SECONDS:
                continue

            message = f"""
#{ticker}

Price: ${price:.2f} • {pct_change:.2f}%

{signal}
"""

            print(f"ALERT: {ticker} → {signal}")
            send_alert(message)

            state[ticker] = now
            save_state(state)

        time.sleep(CHECK_INTERVAL)

# =========================
# START
# =========================


if __name__ == "__main__":
    run()
