import requests
import time
import os
from signal_logic import classify_signal

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

WATCHLIST = ["AMC", "GME", "CVNA", "UPST"]

# 🔒 STATE TRACKING (NEW — CORE OF CONTROL PHASE)
last_state = {}

def send_telegram(msg):
    url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def get_price(symbol):
    try:
        url = "https://finnhub.io/api/v1/quote?symbol=" + symbol + "&token=" + FINNHUB_API_KEY
        r = requests.get(url).json()

        price = r.get("c")
        prev = r.get("pc")

        if not price or not prev:
            return None

        pct = ((price - prev) / prev) * 100
        return price, round(pct, 2)

    except:
        return None

def build_structure(pct):
    if pct >= 8:
        return {"rvol": 3.0, "velocity": "EXTREME"}
    elif pct >= 5:
        return {"rvol": 2.2, "velocity": "ACCELERATING"}
    elif pct >= 6:
        return {"rvol": 2.5, "velocity": "HIGH"}
    elif pct >= 3.5:
        return {"rvol": 1.6, "velocity": "MODERATE"}
    elif pct < 2:
        return {"rvol": 1.5, "velocity": "REVERSING"}
    else:
        return {"rvol": 1.0, "velocity": "LOW"}

def run():
    print("IAL ENGINE LIVE")

    while True:
        for symbol in WATCHLIST:
            print("Checking", symbol)

            data = get_price(symbol)
            if not data:
                continue

            price, pct = data
            structure = build_structure(pct)

            signal = classify_signal(symbol, pct, structure)

            if signal:
                current_state = signal["state"]
                previous_state = last_state.get(symbol)

                # 🔒 CONTROL PHASE LOGIC
                if previous_state == current_state:
                    print(f"⏸ Skipping {symbol} — same state ({current_state})")
                    continue

                message = f"""
{symbol}

Price: {price} • {pct}%

{signal['emoji']} {signal['name']}

Structure:
Volume: {signal['volume']}
Velocity: {signal['velocity']}

State: {signal['state']}

READ:
{signal['read']}
"""
                send_telegram(message)

                # 🔒 UPDATE STATE AFTER SEND
                last_state[symbol] = current_state

        time.sleep(60)

if __name__ == "__main__":
    run()
