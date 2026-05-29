# ===============================
# 📦 IMPORTS
# ===============================
import requests
import time
import json
import os

# ===============================
# 🔐 ENV VARIABLES
# ===============================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

TG_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# ===============================
# 📁 DATA SOURCE
# ===============================
DATA_FILE = "ial_data.json"

# ===============================
# 🔒 SIGNAL FILTER ENGINE
# ===============================
LAST_ALERT = {}
COOLDOWN_SECONDS = 1800  # 30 minutes

def should_alert(symbol, price, change_pct, volume, avg_volume, state):
    now = time.time()

    # 1. COOLDOWN
    last_time = LAST_ALERT.get(symbol, 0)
    if now - last_time < COOLDOWN_SECONDS:
        return False

    # 2. MIN PRICE FILTER
    if price < 2:
        return False

    # 3. MOVE FILTER
    if abs(change_pct) < 3:
        return False

    # 4. VOLUME CONFIRMATION
    if volume < avg_volume * 1.5:
        return False

    # 5. STATE FILTER
    if state not in ["BUILDING", "LOADED"]:
        return False

    # PASS
    LAST_ALERT[symbol] = now
    return True

# ===============================
# 📤 TELEGRAM SENDER
# ===============================
def send_alert(message):
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        requests.post(TG_URL, json=payload, timeout=10)
    except:
        print("Telegram send failed")

# ===============================
# 🧠 LOAD DATA
# ===============================
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

# ===============================
# 🚨 MAIN LOOP
# ===============================
def run_bot():
    print("BOT STARTED...")

    while True:
        data = load_data()

        for symbol, d in data.items():

            price = d.get("price", 0)
            change_pct = d.get("change_pct", 0)
            volume = d.get("volume", 0)
            avg_volume = d.get("avg_volume", 1)
            state = d.get("state", "NONE")

            if should_alert(symbol, price, change_pct, volume, avg_volume, state):

                message = (
                    f"{symbol}\n"
                    f"Price: {price} • {change_pct}%\n\n"
                    f"🔥 {state}\n\n"
                    f"Volume: {volume}"
                )

                print(f"ALERT: {symbol} → {state}")
                send_alert(message)

        time.sleep(60)

# ===============================
# ▶️ START
# ===============================

if __name__ == "__main__":
    run()
