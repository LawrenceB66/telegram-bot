import requests
import json
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

TG_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

DATA_FILE = "ial_data.json"

LAST_ALERT = {}
COOLDOWN_SECONDS = 1800

# ===============================
# FILTER ENGINE
# ===============================
def should_alert(symbol, d):
    now = time.time()

    price = d["price"]
    change_pct = d["change_pct"]
    volume = d["volume"]
    avg_volume = d["avg_volume"]

    # COOLDOWN
    if now - LAST_ALERT.get(symbol, 0) < COOLDOWN_SECONDS:
        return False

    # HARD FILTERS
    if price < 5:
        return False

    if abs(change_pct) < 3:
        return False

    if volume < avg_volume * 1.5:
        return False

    LAST_ALERT[symbol] = now
    return True

# ===============================
# TELEGRAM
# ===============================
def send(msg):
    try:
        requests.post(TG_URL, json={
            "chat_id": CHAT_ID,
            "text": msg
        }, timeout=10)
    except:
        print("SEND FAIL")

# ===============================
# LOAD DATA
# ===============================
def load():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

# ===============================
# MAIN LOOP
# ===============================
def run_bot():
    print("BOT STARTED...\n")

    while True:
        data = load()

        for symbol, d in data.items():

            if should_alert(symbol, d):

                msg = (
                    f"{symbol}\n"
                    f"Price: {d['price']} • {d['change_pct']}%\n\n"
                    f"Volume: {d['volume']}"
                )

                print(f"ALERT: {symbol}")
                send(msg)

        time.sleep(60)


if __name__ == "__main__":
    run()
