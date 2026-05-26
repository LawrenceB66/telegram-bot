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
# STATE TRACKING (MEMORY)
# =========================
symbol_states = {symbol: "BASELINE" for symbol in SYMBOLS}

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
    print("STATE ENGINE ACTIVE")

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

            # =========================
            # ONLY ALERT ON STATE CHANGE
            # =========================
            if new_state != old_state:
                message = format_alert(symbol, price, change_pct, new_state)
                send_telegram_message(message)
                print(f"STATE CHANGE ALERT: {symbol} → {new_state}")

                # update memory
                symbol_states[symbol] = new_state

        time.sleep(60)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    run_bot()
