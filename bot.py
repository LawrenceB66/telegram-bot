print("FILE LOADED")

import requests
import time
import os

# =========================
# ENV VARIABLES
# =========================
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

WATCHLIST = [
    "AMC","GME","CVNA","UPST","NVDA","TSLA","AAPL","MSFT","META","AMD",
    "NFLX","GOOGL","AMZN","COIN","PLTR","AI","RIOT","MARA","SOFI","LCID",
    "NIO","RIVN","SPY","QQQ","IWM","BA","DIS","PYPL","SHOP","SQ",
    "UBER","LYFT","SNAP","PINS","ROKU","FUBO","BABA","JD","XPEV","LI",
    "DKNG","HOOD","AFRM","RUN","ENPH","FSLR","T","VZ","INTC","CSCO"
]

state_memory = {}
structure_memory = {}

# =========================
# PRICE DATA
# =========================
def get_price_data(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        r = requests.get(url).json()

        price = r.get("c")
        pct = r.get("dp")

        if price is None or pct is None:
            return None, None

        return price, pct

    except:
        return None, None

# =========================
# STRUCTURE ENGINE
# =========================
def check_structure(symbol, pct):
    prev = structure_memory.get(symbol, 0)

    if 2 <= pct <= 8:
        structure_memory[symbol] = prev + 1
    else:
        structure_memory[symbol] = 0

    return structure_memory[symbol] >= 2

# =========================
# STATE ENGINE
# =========================
def get_state(symbol, pct_change):
    prev_state = state_memory.get(symbol, "BASELINE")

    if pct_change >= 5:
        new_state = "LOADED"
    elif pct_change >= 2:
        new_state = "BUILDING"
    else:
        new_state = "BASELINE"

    return prev_state, new_state

# =========================
# STATE RANKING (NEW FIX)
# =========================
def state_rank(state):
    ranks = {
        "BASELINE": 0,
        "BUILDING": 1,
        "LOADED": 2
    }
    return ranks.get(state, 0)

# =========================
# SIGNAL
# =========================
def get_signal(state):
    if state == "BUILDING":
        return "🔥 Pressure Cooker"
    elif state == "LOADED":
        return "💣 Ticking Time Bomb"
    return None

# =========================
# VOLUME
# =========================
def get_volume_label(pct_change, state):
    if state == "LOADED":
        return "EXPANDING"
    elif state == "BUILDING":
        return "ELEVATED"
    return "NORMAL"

# =========================
# READ
# =========================
def get_read(state):
    if state == "BUILDING":
        return (
            "Pressure forming beneath the surface. "
            "Repeated movement detected — structure building."
        )
    elif state == "LOADED":
        return (
            "Confirmed pressure expansion. "
            "Momentum aligned with structure — volatility likely."
        )
    return None

# =========================
# FORMAT
# =========================
def format_message(symbol, price, pct, signal, volume, state, read):
    price_str = f"{price:.2f}".rstrip('0').rstrip('.')

    msg = f"{symbol}\n\n"
    msg += f"Price: {price_str} • {pct:.2f}%\n\n"
    msg += f"{signal}\n\n"
    msg += f"Volume: {volume}\n\n"
    msg += f"State: {state}\n\n"
    msg += f"READ:\n{read}"

    return msg

# =========================
# TELEGRAM
# =========================
def send_telegram(message):
    try:
        requests.post(BASE_URL, json={
            "chat_id": CHANNEL_ID,
            "text": message
        })
    except Exception as e:
        print("Telegram error:", e)

# =========================
# MAIN LOOP
# =========================
def run_bot():
    print("BOT STARTED")

    while True:
        for symbol in WATCHLIST:

            price, pct = get_price_data(symbol)
            if price is None:
                continue

            # STRUCTURE FIRST
            if not check_structure(symbol, pct):
                continue

            prev_state, state = get_state(symbol, pct)

            # 🚨 BLOCK DOWNGRADES (CRITICAL FIX)
            if state_rank(state) <= state_rank(prev_state):
                continue

            if state == "BASELINE":
                continue

            signal = get_signal(state)
            if signal is None:
                continue

            volume = get_volume_label(pct, state)
            read = get_read(state)

            message = format_message(
                symbol, price, pct, signal,
                volume, state, read
            )

            send_telegram(message)

            state_memory[symbol] = state

            print(f"ALERT: {symbol} → {state}")

            time.sleep(1)

        time.sleep(30)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    run_bot()
