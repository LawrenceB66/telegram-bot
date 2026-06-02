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
STATE_FILE = "state.json"

# =========================
# TICKERS (~80)
# =========================

TICKERS = [
    "AMC","GME","CVNA","UPST","LCID","RIVN","NIO","XPEV",
    "PLTR","AI","SOFI","HOOD","AFRM","DKNG","OPEN","QS",
    "TLRY","FUBO","NKLA","FFIE","MULN","SINT",
    "MARA","RIOT","COIN",
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA",
    "DIS","BABA","UBER","LYFT","SQ","PYPL","JPM","BAC","WFC",
    "C","GS","MS",
    "SPY","QQQ","IWM",
    "AMD","INTC","CRM","ORCL","ADBE",
    "SHOP","SNOW","DDOG","NET",
    "BA","GE","CAT",
    "XOM","CVX","OXY",
    "PFE","MRNA","JNJ",
    "T","VZ",
    "KO","PEP",
    "WMT","COST","HD","LOW"
]

# =========================
# STATE LOAD/SAVE
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
# FETCH PRICE
# =========================

def get_price(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()

        price = data.get("c")
        prev_close = data.get("pc")

        if price and prev_close:
            pct = ((price - prev_close) / prev_close) * 100
            return round(price, 2), round(pct, 2)
    except:
        pass

    return None, None

# =========================
# STATE LOGIC
# =========================

def classify_state(pct, prev_pct):
    if pct is None:
        return None

    # EXPANSION (⚡️)
    if abs(pct) >= 6:
        return "EXPANSION"

    # BUILDING (🔥)
    if 2 <= pct < 6:
        return "BUILDING"

    # LOADED (💣)
    if pct >= 5:
        return "LOADED"

    # DOWNSIDE (🩸)
    if pct <= -5:
        return "DOWNSIDE"

    return "BASELINE"

# =========================
# EXHAUSTION LOGIC
# =========================

def check_overbought(state, pct, prev_pct):
    if not prev_pct:
        return False

    return (
        pct >= 8 and
        prev_pct > pct and
        state in ["BUILDING", "LOADED", "EXPANSION"]
    )

def check_oversold(state, pct, prev_pct):
    if not prev_pct:
        return False

    return (
        pct <= -8 and
        prev_pct < pct and
        state == "DOWNSIDE"
    )

# =========================
# MESSAGE BUILDER
# =========================

def build_message(symbol, price, pct, state, last_state):
    emoji_map = {
        "BUILDING": "🔥",
        "LOADED": "💣",
        "EXPANSION": "⚡️",
        "DOWNSIDE": "🩸",
        "OVERBOUGHT": "🥵",
        "OVERSOLD": "❄️"
    }

    label_map = {
        "BUILDING": "Building",
        "LOADED": "Loaded",
        "EXPANSION": "Expansion",
        "DOWNSIDE": "Downside",
        "OVERBOUGHT": "Overbought",
        "OVERSOLD": "Oversold"
    }

    emoji = emoji_map.get(state, "")
    label = label_map.get(state, state)

    message = (
        f"#{symbol}\n\n"
        f"Price: ${price} • {pct}%\n\n"
        f"{emoji} {label}\n\n"
        f"State: {state}"
    )

    return message

# =========================
# MAIN LOOP
# =========================

def run():
    print("STATE ENGINE ACTIVE")

    state_data = load_state()

    while True:
        for ticker in TICKERS:
            price, pct = get_price(ticker)

            if pct is None:
                continue

            prev = state_data.get(ticker, {})
            prev_state = prev.get("state")
            prev_pct = prev.get("pct")

            base_state = classify_state(pct, prev_pct)

            # CHECK EXHAUSTION
            if check_overbought(prev_state, pct, prev_pct):
                current_state = "OVERBOUGHT"
            elif check_oversold(prev_state, pct, prev_pct):
                current_state = "OVERSOLD"
            else:
                current_state = base_state

            # ONLY SEND ON STATE CHANGE
            if current_state != prev_state:
                msg = build_message(ticker, price, pct, current_state, prev_state)
                send_alert(msg)
                print(f"ALERT: {ticker} → {current_state}")

            # SAVE STATE
            state_data[ticker] = {
                "state": current_state,
                "pct": pct,
                "price": price,
                "timestamp": time.time()
            }

            time.sleep(1)

        save_state(state_data)
        print("Cycle complete. Waiting...")
        time.sleep(CHECK_INTERVAL)

# =========================
# START
# =========================

if __name__ == "__main__":
    run()
