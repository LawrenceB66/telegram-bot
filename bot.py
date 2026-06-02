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

# ============================
# EXPANDED TICKER LIST
# ============================

TICKERS = [
    "AMC","GME","CVNA","UPST","LCID","RIVN","NIO","XPEV",
    "SOFI","HOOD","AFRM","DKNG","OPEN","QS",
    "MARA","RIOT","COIN",
    "NVDA","PLTR","AI","MSFT","GOOGL","AMZN","META","TSLA",
    "AAPL","SPY","QQQ",
    "FFIE","MULN","NKLA","SNDL","TLRY","FUBO",
    "JPM","BAC","WFC","GS","MS","C"
]

# ============================
# STATE RANKING (ANTI-SPAM)
# ============================

STATE_RANK = {
    "BASELINE": 0,
    "BUILDING": 1,
    "LOADED": 2,
    "EXTENDED": 3
}

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

def get_price_data(ticker):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_API_KEY}"
        r = requests.get(url, timeout=5)
        data = r.json()

        price = data.get("c", 0)
        prev_close = data.get("pc", 0)

        if price == 0 or prev_close == 0:
            return None

        change_pct = ((price - prev_close) / prev_close) * 100

        return price, change_pct
    except:
        return None

# ============================
# STATE CLASSIFICATION
# ============================

def get_state(change_pct):
    abs_change = abs(change_pct)

    if abs_change < 1:
        return "BASELINE"
    elif abs_change < 3:
        return "BUILDING"
    elif abs_change < 6:
        return "LOADED"
    else:
        return "EXTENDED"

# ============================
# SIGNAL BUILDERS
# ============================

def build_breakout(ticker, price, change_pct):
    return (
        f"#{ticker}\n"
        f"Price: ${price:.2f} • {change_pct:.2f}%\n\n"
        f"🚀 Breakout Alert\n\n"
        f"Structure:\n"
        f"SI: N/A • DTC: N/A\n"
        f"Volume: EXPANDING\n\n"
        f"State: EXTENDED\n\n"
        f"READ:\n"
        f"Expansion is underway. Momentum and participation are accelerating. This is not early-stage pressure — this is active movement."
    )

def build_exhaustion(ticker, price, change_pct):
    return (
        f"#{ticker}\n"
        f"Price: ${price:.2f} • {change_pct:.2f}%\n\n"
        f"🩸 Overbought\n\n"
        f"Structure:\n"
        f"SI: N/A • DTC: N/A\n"
        f"Volume: ELEVATED\n\n"
        f"State: EXTENDED\n\n"
        f"READ:\n"
        f"Momentum is weakening following expansion. Early signs of exhaustion are present. This is where profit-taking and pullbacks begin to emerge."
    )

# ============================
# MAIN ENGINE
# ============================

def run():
    print("🚀 SIGNAL ENGINE ACTIVE")

    state = load_state()

    while True:
        now = time.time()

        for ticker in TICKERS:

            data = get_price_data(ticker)
            if not data:
                continue

            price, change_pct = data

            if ticker not in state:
                state[ticker] = {
                    "state": "BASELINE",
                    "last_alert": 0
                }
                continue

            prev_state = state[ticker]["state"]
            last_alert = state[ticker]["last_alert"]

            current_state = get_state(change_pct)

            # ============================
            # SIGNAL LOGIC
            # ============================

            signal = None

            # 🚀 BREAKOUT (override)
            if current_state == "EXTENDED" and change_pct >= 10:
                signal = build_breakout(ticker, price, change_pct)

            # 🩸 EXHAUSTION
            elif prev_state == "EXTENDED" and change_pct <= -3:
                signal = build_exhaustion(ticker, price, change_pct)

            # ============================
            # ALERT CONTROL
            # ============================

            if signal:
                if now - last_alert > COOLDOWN_SECONDS:
                    send_alert(signal)
                    state[ticker]["last_alert"] = now
                    print(f"ALERT: {ticker}")

            # ============================
            # STATE UPDATE
            # ============================

            state[ticker]["state"] = current_state

        save_state(state)

        print("🧠 Cycle complete. Waiting...")
        time.sleep(CHECK_INTERVAL)

# ============================
# START
# ============================

if __name__ == "__main__":
    run()
