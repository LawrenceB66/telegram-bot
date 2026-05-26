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
# STATE TRACKING
# =========================
symbol_states = {symbol: "BASELINE" for symbol in SYMBOLS}
last_alert_time = {symbol: 0 for symbol in SYMBOLS}

COOLDOWN_SECONDS = 300  # 5 minutes

# =========================
# TELEGRAM FUNCTION
# =========================
def send_telegram_message(message):
    try:
        payload = {
            "chat_id": CHAT_ID,
            "text": message
        }
        response = requests.post(TG_URL, data=payload, timeout=10)
        print("TELEGRAM RESPONSE:", response.text)
    except Exception as e:
        print("TELEGRAM ERROR:", e)

# =========================
# GET STOCK DATA
# =========================
def get_quote(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        response = requests.get(url, timeout=10)
        return response.json()
    except Exception as e:
        print(f"ERROR FETCHING {symbol}:", e)
        return None

# =========================
# STATE LOGIC
# =========================
def determine_state(change_pct):
    if abs(change_pct) < 2:
        return "BASELINE"
    elif abs(change_pct) < 5:
        return "BUILDING"
    else:
        return "LOADED"

# =========================
# STATE RANK (FOR DIRECTION)
# =========================
state_rank = {
    "BASELINE": 0,
    "BUILDING": 1,
    "LOADED": 2
}

# =========================
# FORMAT ALERT
# =========================
def format_alert(symbol, price, change_pct, state):
    emoji_map = {
        "BASELINE": "🧊",
        "BUILDING": "🔥",
        "LOADED": "💣"
    }

    return (
        f"{symbol}\n"
        f"Price: {price:.2f}\n"
        f"Change: {change_pct:.2f}%\n\n"
        f"{emoji_map[state]} {state}"
    )

# =========================
# MAIN LOOP
# =========================
def run_bot():
    print("LOCKED STATE ENGINE ACTIVE")

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

            print(f"{symbol} | {change_pct:.2f}% | {old_state} → {new_state}")

            current_time = time.time()

            # =========================
            # CONDITIONS TO ALERT
            # =========================
            is_state_upgrade = state_rank[new_state] > state_rank[old_state]
            cooldown_passed = (current_time - last_alert_time[symbol]) > COOLDOWN_SECONDS

            if is_state_upgrade and cooldown_passed:
                message = format_alert(symbol, price, change_pct, new_state)
                send_telegram_message(message)

                print(f"UPGRADE ALERT: {symbol} → {new_state}")

                symbol_states[symbol] = new_state
                last_alert_time[symbol] = current_time

            else:
                # Update state silently (no alert on downgrade)
                symbol_states[symbol] = new_state

        time.sleep(60)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    run_bot()
