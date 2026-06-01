import requests
import time
import os
import json

from send_alert import send_alert

# ==============================
# CONFIG
# ==============================

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

CHECK_INTERVAL = 30
COOLDOWN_SECONDS = 300

TICKERS = [
    "AMC","GME","CVNA","UPST","LCID","RIVN","NIO","XPEV","PLTR","AI",
    "SOFI","HOOD","AFRM","DKNG","OPEN","QS","MARA","RIOT","COIN","SNDL",
    "TLRY","FUBO","NKLA","FFIE","MULN","SINT","WOK",

    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","AMD","INTC","NFLX",
    "DIS","BABA","UBER","LYFT","SQ","PYPL","SHOP","CRM","ORCL","ADBE",

    "JPM","BAC","WFC","C","GS","MS","BLK","AXP","SCHW","COF",

    "XOM","CVX","OXY","SLB","HAL","COP","BP","TOT","EOG","DVN",

    "BA","GE","CAT","DE","LMT","RTX","NOC","HON","UPS","FDX",

    "KO","PEP","MCD","SBUX","WMT","TGT","COST","HD","LOW","DG",

    "PFE","MRNA","JNJ","UNH","ABBV","LLY","BMY","GILD","CVS","WBA",

    "SPY","QQQ","IWM","DIA","ARKK","XLF","XLE","XLK","XLV","XLY",

    "JD","PDD","BIDU","TME","NTES","LI","XPEV","TSM","ASML",

    "SNAP","ROKU","PINS","TTD","ZM","DOCU","OKTA","CRWD","ZS","NET",

    "PANW","DDOG","MDB","SNOW","U","PATH","RBLX","COUP","HUBS","TEAM"
]

STATE_FILE = "state.json"

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

# ==============================
# DATA FETCH
# ==============================

def get_data(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()

        price = data.get("c", 0)
        prev_close = data.get("pc", 0)

        if price == 0 or prev_close == 0:
            return None

        change_pct = ((price - prev_close) / prev_close) * 100

        return {
            "price": round(price, 2),
            "change_pct": round(change_pct, 2)
        }

    except:
        return None

# ==============================
# CLASSIFIER
# ==============================

def classify(change_pct):
    if change_pct >= 6:
        return "🚀 BREAKOUT"
    elif change_pct >= 3.5:
        return "🔥 BUILDING"
    elif change_pct <= -3.5:
        return "📉 DOWNSIDE"
    else:
        return None

# ==============================
# STATE
# ==============================

def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# ==============================
# MAIN LOOP
# ==============================

def run():
    print("BOT STARTED...")

    state = load_state()

    while True:
        for symbol in TICKERS:
            data = get_data(symbol)

            if not data:
                continue

            price = data["price"]
            change_pct = data["change_pct"]
            new_state = classify(change_pct)

            if not new_state:
                continue

            last = state.get(symbol, {})
            last_state = last.get("state")
            last_time = last.get("time", 0)

            now = time.time()

            if new_state == last_state:
                continue

            if now - last_time < COOLDOWN_SECONDS:
                continue

            message = (
                f"#{symbol}\n"
                f"Price: ${price} • {change_pct}%\n\n"
                f"{new_state}"
            )

            print(f"ALERT: {symbol} → {new_state}")
            send_alert(message)

            state[symbol] = {
                "state": new_state,
                "time": now
            }

        save_state(state)
        time.sleep(CHECK_INTERVAL)

# ==============================
# START
# ==============================

if __name__ == "__main__":
    run()
