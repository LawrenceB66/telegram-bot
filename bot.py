import requests
import time

# =========================
# ENV VARIABLES
# =========================
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHANNEL_ID = "YOUR_CHANNEL_ID"

FINNHUB_API_KEY = "YOUR_FINNHUB_API_KEY"
FMP_API_KEY = "YOUR_FMP_API_KEY"

BASE_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

WATCHLIST = ["AMC", "CVNA", "UPST"]

# =========================
# STATE MEMORY (LOCKED)
# =========================
state_memory = {}

# =========================
# DATA FETCHING
# =========================
def get_price_data(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        r = requests.get(url).json()
        return r.get("c"), r.get("dp")
    except:
        return None, None

def get_si_dtc(symbol):
    try:
        url = f"https://financialmodelingprep.com/api/v4/short_interest?symbol={symbol}&apikey={FMP_API_KEY}"
        r = requests.get(url).json()

        if isinstance(r, list) and len(r) > 0:
            si = r[0].get("shortPercentFloat", 0)
            dtc = r[0].get("daysToCover", 0)
            return si, dtc
    except:
        pass

    return 0, 0

# =========================
# STATE ENGINE (LOCKED — DO NOT MOVE MEMORY WRITE)
# =========================
def get_state(symbol, pct_change):
    prev_state = state_memory.get(symbol, "BASELINE")

    if pct_change >= 5:
        new_state = "LOADED"
    elif pct_change >= 2:
        new_state = "BUILDING"
    else:
        new_state = "BASELINE"

    # 🔒 CRITICAL — MUST STAY HERE
    state_memory[symbol] = new_state

    return prev_state, new_state

# =========================
# STRUCTURE VALIDATION (YOUR RULES)
# =========================
def validate_structure(si, dtc, state):
    if state == "BUILDING":
        return si >= 15 and dtc >= 3
    elif state == "LOADED":
        return si >= 20 and dtc >= 5
    return False

# =========================
# SIGNAL MAPPING (LOCKED)
# =========================
def get_signal(state):
    if state == "BUILDING":
        return "🔥 Pressure Cooker"
    elif state == "LOADED":
        return "💣 Ticking Time Bomb"
    return None

# =========================
# VOLUME CLASSIFICATION
# =========================
def get_volume_label(state):
    if state == "LOADED":
        return "EXPANDING"
    elif state == "BUILDING":
        return "ELEVATED"
    return "NORMAL"

# =========================
# READ BLOCK (STATIC — DO NOT CHANGE)
# =========================
def get_read(state):
    if state == "BUILDING":
        return ("Short pressure is actively building. "
                "Liquidity and positioning are tightening. "
                "This is where setups begin forming — attention required.")
    elif state == "LOADED":
        return ("Pressure conditions are fully developed. "
                "Positioning is constrained and unstable. "
                "High potential for volatility expansion.")
    return None

# =========================
# MESSAGE FORMAT (LOCKED — EXACT STRUCTURE)
# =========================
def format_message(symbol, price, pct, signal, si, dtc, volume, state, read):

    price_str = f"{price:.2f}".rstrip('0').rstrip('.')

    msg = f"{symbol}\n\n"
    msg += f"Price: {price_str} • {pct:.2f}%\n\n"

    msg += f"{signal}\n\n"

    msg += f"Structure:\n"
    msg += f"SI: {int(si)}% • DTC: {int(dtc)}\n"
    msg += f"Volume: {volume}\n\n"

    msg += f"State: {state}\n\n"

    msg += f"READ:\n{read}"

    return msg

# =========================
# TELEGRAM SEND
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
# MAIN LOOP (LOCKED FLOW)
# =========================
def run_bot():
    while True:
        for symbol in WATCHLIST:

            price, pct = get_price_data(symbol)
            if price is None or pct is None:
                continue

            si, dtc = get_si_dtc(symbol)

            prev_state, state = get_state(symbol, pct)

            # BASELINE = NO ALERT
            if state == "BASELINE":
                continue

            # STRUCTURE REQUIRED
            if not validate_structure(si, dtc, state):
                continue

            # STATE CHANGE REQUIRED
            if state == prev_state:
                continue

            signal = get_signal(state)
            if signal is None:
                continue

            volume = get_volume_label(state)
            read = get_read(state)

            message = format_message(
                symbol, price, pct, signal,
                si, dtc, volume, state, read
            )

            send_telegram(message)

            print(f"ALERT: {symbol} → {state}")

            time.sleep(1)

        time.sleep(30)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    run_bot()
