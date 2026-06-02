import requests
import time
import json
import os

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

STATE_FILE = "state.json"

CHECK_INTERVAL = 30
COOLDOWN_SECONDS = 300

PHASE_RESET_SECONDS = 1800  # 30 minutes
RESET_THRESHOLD = 2.0       # % reset threshold

# =========================
# TICKER LIST (80)
# =========================

TICKERS = [
    "AMC","GME","CVNA","UPST","SOFI","HOOD","AFRM","DKNG",
    "MARA","RIOT","COIN","WOK","MULN","SINT","FFIE","NKLA",
    "SNDL","TLRY","FUBO","OPEN","QS","AI","PLTR",
    "LCID","RIVN","NIO","XPEV",
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA",
    "AMD","INTC","SMCI","ADBE","CRM","NFLX","ORCL",
    "UBER","LYFT","SHOP","SQ","PYPL","ROKU","SNAP",
    "BABA","JD","PDD","TME","DIS","PARA","WBD",
    "BA","GE","CAT","F","GM","T","VZ",
    "SPY","QQQ","IWM",
    "XOM","CVX","OXY",
    "JPM","BAC","GS","MS",
    "COIN","MSTR","BITO"
]

# =========================
# STATE LOAD / SAVE
# =========================

def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# =========================
# TELEGRAM
# =========================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=payload)

# =========================
# PRICE FETCH
# =========================

def get_price_data(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={os.getenv('FINNHUB_API_KEY')}"
        r = requests.get(url).json()

        price = r.get("c")
        prev = r.get("pc")

        if not price or not prev:
            return None

        pct = ((price - prev) / prev) * 100
        return price, round(pct, 2)

    except:
        return None

# =========================
# STATE LOGIC
# =========================

def determine_state(change_pct):
    if abs(change_pct) >= 10:
        return "EXTENDED"
    elif abs(change_pct) >= 5:
        return "LOADED"
    elif abs(change_pct) >= 2:
        return "BUILDING"
    else:
        return "BASELINE"

# =========================
# MESSAGE FORMAT
# =========================

def format_message(symbol, price, pct, state, phase_text):
    return f"""#{symbol}
Price: ${price:.2f} • {pct:+.2f}%

State: {state}

{phase_text}
"""

# =========================
# MAIN ENGINE
# =========================

def run():

    state_data = load_state()

    print("🚀 IAL PHASE ENGINE STARTED")
    print("Scanner running...")

    while True:

        for symbol in TICKERS:

            data = get_price_data(symbol)
            if not data:
                continue

            price, pct = data
            current_state = determine_state(pct)

            now = time.time()

            t = state_data.get(symbol, {
                "last_state": None,
                "last_alert_time": 0,
                "phase_start_price": None,
                "phase_count": 0
            })

            # =========================
            # RESET LOGIC
            # =========================

            reset = False

            # TIME RESET
            if now - t["last_alert_time"] > PHASE_RESET_SECONDS:
                reset = True

            # MOMENTUM RESET
            if t["phase_start_price"]:
                move = abs((price - t["phase_start_price"]) / t["phase_start_price"] * 100)
                if move < RESET_THRESHOLD:
                    reset = True

            if reset:
                t["phase_start_price"] = None
                t["phase_count"] = 0

            # =========================
            # STATE FILTER (NO SPAM)
            # =========================

            if current_state == t["last_state"]:
                continue

            if current_state == "BASELINE":
                t["last_state"] = current_state
                state_data[symbol] = t
                continue

            # =========================
            # PHASE TRACKING
            # =========================

            if t["phase_start_price"] is None:
                t["phase_start_price"] = price
                t["phase_count"] = 1
                phase_text = ""
            else:
                t["phase_count"] += 1
                change_since = ((price - t["phase_start_price"]) / t["phase_start_price"]) * 100
                phase_text = f"Since Alert: {change_since:+.2f}% • #{t['phase_count']}"

            # =========================
            # SEND
            # =========================

            msg = format_message(symbol, price, pct, current_state, phase_text)
            send_telegram(msg)

            print(f"ALERT: {symbol} | {current_state}")

            # =========================
            # SAVE STATE
            # =========================

            t["last_state"] = current_state
            t["last_alert_time"] = now

            state_data[symbol] = t
            save_state(state_data)

            time.sleep(1)

        print("Cycle complete. Waiting...")
        time.sleep(CHECK_INTERVAL)

# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        time.sleep(5)
