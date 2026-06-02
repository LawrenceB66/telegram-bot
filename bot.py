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

# 🔥 CONTEXT EXPIRY (4 HOURS)
CONTEXT_EXPIRY = 14400

STATE_FILE = "state.json"

# ============================
# 80 TICKERS
# ============================

TICKERS = [
"AMC","GME","CVNA","UPST","LCID","RIVN","NIO","XPEV",
"SOFI","HOOD","AFRM","DKNG","OPEN","QS",
"MARA","RIOT","COIN",
"NVDA","PLTR","AI","MSFT","GOOGL","AMZN","META","TSLA",
"AAPL","SPY","QQQ",
"FFIE","MULN","NKLA","SNDL","TLRY","FUBO",
"JPM","BAC","WFC","GS","MS","C",
"AMD","INTC","CRM","ADBE","ORCL","CSCO","IBM","NOW",
"SNOW","DDOG","ZS","NET","CRWD","OKTA","PANW","MDB",
"COST","WMT","TGT","HD","LOW","NKE","SBUX","MCD",
"XOM","CVX","OXY","SLB","COP","HAL","EOG","DVN"
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

def reset_context(state, ticker):
    state[ticker]["alert_count"] = 0
    state[ticker]["alert_price"] = 0

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
# STATE LOGIC
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
# MESSAGE BUILDERS
# ============================

def build_breakout(ticker, price, change_pct, since_text):
    return (
        f"#{ticker}\n\n"
        f"Price: ${price:.2f} • {change_pct:.2f}%\n"
        f"{since_text}\n\n"
        f"🚀 Breakout Alert\n\n"
        f"Structure:\n"
        f"SI: N/A • DTC: N/A\n"
        f"Volume: EXPANDING\n\n"
        f"State: EXTENDED\n\n"
        f"READ:\n"
        f"Expansion is underway."
    )

def build_exhaustion(ticker, price, change_pct, since_text):
    return (
        f"#{ticker}\n\n"
        f"Price: ${price:.2f} • {change_pct:.2f}%\n"
        f"{since_text}\n\n"
        f"🩸 Overbought\n\n"
        f"Structure:\n"
        f"SI: N/A • DTC: N/A\n"
        f"Volume: ELEVATED\n\n"
        f"State: EXTENDED\n\n"
        f"READ:\n"
        f"Momentum weakening. Signs of exhaustion are present."
    )

# ============================
# MAIN ENGINE
# ============================

def run():
    print("🚀 MOMENTUM PHASE ENGINE ACTIVE")

    state = load_state()

    while True:
        now = time.time()

        for ticker in TICKERS:

            data = get_price_data(ticker)
            if not data:
                continue

            price, change_pct = data

            # INIT
            if ticker not in state:
                state[ticker] = {
                    "state": "BASELINE",
                    "last_alert": 0,
                    "alert_price": 0,
                    "alert_count": 0
                }
                continue

            prev_state = state[ticker]["state"]
            last_alert = state[ticker]["last_alert"]

            current_state = get_state(change_pct)

            signal = None
            since_text = ""

            # ============================
            # 🔥 DUAL RESET SYSTEM
            # ============================

            # TIME RESET
            if now - last_alert > CONTEXT_EXPIRY:
                reset_context(state, ticker)

            # UPSIDE STRUCTURE RESET
            if change_pct < 10:
                reset_context(state, ticker)

            # DOWNSIDE STRUCTURE RESET
            if change_pct > -5:
                reset_context(state, ticker)

            # ============================
            # SIGNAL LOGIC
            # ============================

            # 🚀 BREAKOUT
            if change_pct >= 10:

                if now - last_alert > COOLDOWN_SECONDS:

                    if state[ticker]["alert_count"] == 0:
                        state[ticker]["alert_price"] = price
                        state[ticker]["alert_count"] = 1
                    else:
                        alert_price = state[ticker]["alert_price"]
                        pct_since = ((price - alert_price) / alert_price) * 100
                        state[ticker]["alert_count"] += 1
                        since_text = f"Since Alert: {pct_since:+.2f}% • #{state[ticker]['alert_count']}"

                    signal = build_breakout(ticker, price, change_pct, since_text)

            # 🩸 EXHAUSTION
            elif change_pct <= -5:

                if now - last_alert > COOLDOWN_SECONDS:

                    if state[ticker]["alert_count"] > 0:
                        alert_price = state[ticker]["alert_price"]
                        pct_since = ((price - alert_price) / alert_price) * 100
                        state[ticker]["alert_count"] += 1
                        since_text = f"Since Alert: {pct_since:+.2f}% • #{state[ticker]['alert_count']}"

                    signal = build_exhaustion(ticker, price, change_pct, since_text)

            # ============================
            # SEND ALERT
            # ============================

            if signal:
                send_alert(signal)
                state[ticker]["last_alert"] = now
                print(f"ALERT: {ticker}")

            state[ticker]["state"] = current_state

            time.sleep(0.4)

        save_state(state)

        print("🧠 Cycle complete. Waiting...")
        time.sleep(CHECK_INTERVAL)

# ============================
# START
# ============================

if __name__ == "__main__":
    run()
