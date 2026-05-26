import requests
import time
import os

# =========================
# ENV VARIABLES
# =========================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

TG_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# =========================
# WATCHLIST
# =========================
SYMBOLS = ["AMC", "CVNA", "UPST"]

# =========================
# STATE MEMORY
# =========================
symbol_states = {symbol: "BASELINE" for symbol in SYMBOLS}
last_alert_time = {symbol: 0 for symbol in SYMBOLS}

# 🔒 HARD ENFORCEMENT
COOLDOWN_SECONDS = 600  # 10 minutes (adjust later)

# =========================
# STATE RANKING
# =========================
state_rank = {
    "BASELINE": 0,
    "BUILDING": 1,
    "LOADED": 2
}

# =========================
# TELEGRAM
# =========================
def send_telegram_message(message):
    try:
        payload = {
            "chat_id": CHAT_ID,
            "text": message
        }
        requests.post(TG_URL, data=payload, timeout=10)
    except Exception as e:
        print("TELEGRAM ERROR:", e)

# =========================
# FETCH DATA
# =========================
def get_quote(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        response = requests.get(url, timeout=10)
        return response.json()
    except:
        return None

# =========================
# STATE LOGIC (TEMP)
# =========================
def determine_state(change_pct):
    if abs(change_pct) < 2:
        return "BASELINE"
    elif abs(change_pct) < 5:
        return "BUILDING"
    else:
        return "LOADED"

# =========================
# MESSAGE FORMAT (UNCHANGED STRUCTURE)
# =========================
def format_alert(symbol, price, change_pct, state):
    if state == "BUILDING":
        state_line = "🔥 Pressure Cooker"
    elif state == "LOADED":
        state_line = "💣 Ticking Time Bomb"
    else:
        state_line = "⚪️ Baseline"

    return (
        f"{symbol}\n\n"
        f"Price: {price:.2f} • {change_pct:.2f}%\n\n"
        f"{state_line}"
    )

# =========================
# MAIN LOOP
# =========================
def run_bot():
    print("HARD ENFORCEMENT ENGINE ACTIVE")

    while True:
        for symbol in SYMBOLS:
            data = get_quote(symbol)
            if not data:
                continue

            price = data.get("c")
            prev_close = data.get("pc")
            if not price or not prev_close:
                continue

            change_pct = ((price - prev_close) / prev_close) * 100

            new_state = determine_state(change_pct)
            old_state = symbol_states[symbol]

            current_time = time.time()

            # =========================
            # 🔒 HARD ENFORCEMENT LOGIC
            # =========================
            is_upgrade = state_rank[new_state] > state_rank[old_state]
            cooldown_passed = (current_time - last_alert_time[symbol]) >= COOLDOWN_SECONDS

            print(f"{symbol} | {old_state} → {new_state} | Upgrade: {is_upgrade} | Cooldown: {cooldown_passed}")

            if is_upgrade and cooldown_passed:
                message = format_alert(symbol, price, change_pct, new_state)
                send_telegram_message(message)

                print(f"ALERT FIRED: {symbol} → {new_state}")

                # 🔒 LOCK MEMORY
                symbol_states[symbol] = new_state
                last_alert_time[symbol] = current_time

            else:
                # Update state silently (no alert)
                symbol_states[symbol] = new_state

        time.sleep(60)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    run_bot()
