import requests
import time
import os
import json

from send_alert import send_alert

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

CHECK_INTERVAL = 30
COOLDOWN_SECONDS = 300

STATE_FILE = "state.json"

# 🔥 EXPANDED 80 TICKER LIST
TICKERS = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","AMD","INTC","NFLX",
    "PLTR","AI","COIN","MARA","RIOT","HOOD","SOFI","DKNG","AFRM","UPST",
    "CVNA","OPEN","QS","LCID","RIVN","NIO","XPEV","FUBO","SNDL","TLRY",
    "AMC","GME","FFIE","MULN","SINT","WOK","NKLA","BB","BYND","ROKU",
    "SHOP","SQ","PYPL","UBER","LYFT","SNAP","PINS","SPOT","ZM","DOCU",
    "BABA","JD","TME","DIS","BA","GE","XOM","CVX","ENPH","SEDG",
    "TSM","ASML","ORCL","CRM","ADBE","PANW","CRWD","ZS","OKTA","NET",
    "DDOG","SNOW","MDB","TEAM","INTU","WDAY","FSLY","ESTC","PATH","C3AI"
]

# ---------------- STATE MANAGEMENT ---------------- #

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# ---------------- DATA FETCH ---------------- #

def get_price(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        return data.get("c"), data.get("dp")
    except:
        return None, None

# ---------------- STATE ENGINE ---------------- #

def determine_state(pct):
    if pct is None:
        return "BASELINE"

    if pct >= 10:
        return "EXPANSION"
    elif pct >= 5:
        return "LOADED"
    elif pct >= 2:
        return "BUILDING"
    elif pct <= -10:
        return "OVERSOLD"
    elif pct <= -5:
        return "DOWNSIDE"
    elif pct <= -2:
        return "OVERBOUGHT"
    else:
        return "BASELINE"

# ---------------- MESSAGE BUILDER ---------------- #

def build_message(symbol, price, pct, state):
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

    price_str = f"{price:.2f}" if price else "N/A"
    pct_str = f"{pct:.2f}" if pct else "0.00"

    # 🔒 BASELINE = ONLY STATE (NO DUPLICATION)
    if state == "BASELINE":
        return (
            f"#{symbol}\n\n"
            f"Price: ${price_str} • {pct_str}%\n\n"
            f"State: BASELINE"
        )

    # 🔥 ALL OTHER STATES = EMOJI + LABEL ONLY
    emoji = emoji_map.get(state, "")
    label = label_map.get(state, state)

    return (
        f"#{symbol}\n\n"
        f"Price: ${price_str} • {pct_str}%\n\n"
        f"{emoji} {label}"
    )

# ---------------- MAIN LOOP ---------------- #

def run():
    print("STATE ENGINE ACTIVE")

    state_data = load_state()

    while True:
        for symbol in TICKERS:
            price, pct = get_price(symbol)

            if price is None:
                continue

            current_state = determine_state(pct)

            last_state = state_data.get(symbol, {}).get("state")

            # 🔒 ONLY SEND ON STATE CHANGE
            if current_state != last_state:
                message = build_message(symbol, price, pct, current_state)

                print(f"ALERT: {symbol} → {current_state}")
                send_alert(message)

                state_data[symbol] = {
                    "state": current_state,
                    "last_price": price,
                    "timestamp": time.time()
                }

                save_state(state_data)

                time.sleep(1)

        print("Cycle complete. Waiting...")
        time.sleep(CHECK_INTERVAL)

# ---------------- START ---------------- #

if __name__ == "__main__":
    run()
