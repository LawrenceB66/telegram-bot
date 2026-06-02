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
STRUCTURE_FILE = "ial_data.json"

CHECK_INTERVAL = 30

PHASE_RESET_SECONDS = 1800
RESET_THRESHOLD = 2.0

# =========================
# TICKERS
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
    "MSTR","BITO"
]

# =========================
# LOADERS
# =========================

def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(data):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_structure():
    if not os.path.exists(STRUCTURE_FILE):
        return {}
    with open(STRUCTURE_FILE, "r") as f:
        return json.load(f)

# =========================
# TELEGRAM
# =========================

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# =========================
# PRICE
# =========================

def get_price(symbol):
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
# STRUCTURE ENGINE (STRICT)
# =========================

def get_signal(symbol, pct, structure):

    data = structure.get(symbol)

    # STRICT MODE — NO STRUCTURE = NO ALERT
    if not data:
        return None

    si = data.get("si")
    dtc = data.get("dtc")

    if si is None or dtc is None:
        return None

    # =========================
    # TIME BOMB EXTENDED
    # =========================
    if si >= 20 and dtc >= 5 and abs(pct) >= 10:
        return {
            "name": "💣 Ticking Time Bomb",
            "state": "EXTENDED",
            "volume": "EXPANDING",
            "si": si,
            "dtc": dtc,
            "read": "Pressure conditions are fully developed. Positioning is constrained and unstable. High potential for volatility expansion."
        }

    # =========================
    # TIME BOMB LOADED
    # =========================
    if si >= 20 and dtc >= 5 and abs(pct) >= 5:
        return {
            "name": "💣 Ticking Time Bomb",
            "state": "LOADED",
            "volume": "EXPANDING",
            "si": si,
            "dtc": dtc,
            "read": "Pressure conditions are fully developed. Positioning is constrained and unstable. High potential for volatility expansion."
        }

    # =========================
    # PRESSURE COOKER
    # =========================
    if si >= 15 and dtc >= 3 and abs(pct) >= 2:
        return {
            "name": "🔥 Pressure Cooker",
            "state": "BUILDING",
            "volume": "ELEVATED",
            "si": si,
            "dtc": dtc,
            "read": "Short pressure is actively building. Liquidity and positioning are tightening. This is where setups begin forming — attention required."
        }

    return None

# =========================
# MESSAGE
# =========================

def format_message(symbol, price, pct, sig, phase):

    return f"""#{symbol}
Price: ${price:.2f} • {pct:+.2f}%

{sig['name']}

Structure:
SI: {sig['si']}% • DTC: {sig['dtc']}
Volume: {sig['volume']}

State: {sig['state']}

READ:
{sig['read']}

{phase}
"""

# =========================
# MAIN LOOP
# =========================

def run():

    state = load_state()
    structure = load_structure()

    print("🚀 IAL STRUCTURE ENGINE LIVE")

    while True:

        for symbol in TICKERS:

            result = get_price(symbol)
            if not result:
                continue

            price, pct = result

            sig = get_signal(symbol, pct, structure)

            if not sig:
                continue  # STRICT MODE BLOCK

            now = time.time()

            t = state.get(symbol, {
                "last_state": None,
                "phase_start_price": None,
                "phase_count": 0,
                "last_alert_time": 0
            })

            # =========================
            # RESET LOGIC
            # =========================

            reset = False

            if now - t["last_alert_time"] > PHASE_RESET_SECONDS:
                reset = True

            if t["phase_start_price"]:
                move = abs((price - t["phase_start_price"]) / t["phase_start_price"] * 100)
                if move < RESET_THRESHOLD:
                    reset = True

            if reset:
                t["phase_start_price"] = None
                t["phase_count"] = 0

            # =========================
            # STATE CHANGE ONLY
            # =========================

            if sig["state"] == t["last_state"]:
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
                move = ((price - t["phase_start_price"]) / t["phase_start_price"]) * 100
                phase_text = f"Since Alert: {move:+.2f}% • #{t['phase_count']}"

            # =========================
            # SEND
            # =========================

            msg = format_message(symbol, price, pct, sig, phase_text)
            send_telegram(msg)

            print(f"ALERT: {symbol} | {sig['state']}")

            t["last_state"] = sig["state"]
            t["last_alert_time"] = now

            state[symbol] = t
            save_state(state)

            time.sleep(1)

        print("Cycle complete. Waiting...")
        time.sleep(CHECK_INTERVAL)

# =========================
# START
# =========================

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"ERROR: {e}")
        time.sleep(5)
