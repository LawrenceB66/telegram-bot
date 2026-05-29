import requests
import time
import json
import os

# =========================
# 🔐 ENV VARIABLES
# =========================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# =========================
# ⚙️ SETTINGS
# =========================
DATA_FILE = "ial_data.json"
CHECK_INTERVAL = 60  # seconds

# =========================
# 📤 SEND ALERT
# =========================
def send_alert(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

# =========================
# 📥 LOAD DATA
# =========================
def load_data():
    if not os.path.exists(DATA_FILE):
        print("No data file found.")
        return {}

    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Load error: {e}")
        return {}

# =========================
# 🧠 ALERT LOGIC
# =========================
def should_alert(symbol, price, change_pct, volume, avg_volume):
    if change_pct < 3.5:
        return False
    if volume < avg_volume:
        return False
    return True

# =========================
# 🔁 PROCESS MARKET
# =========================
def process_market():
    data = load_data()

    if not data:
        print("No data to process.")
        return

    for symbol, d in data.items():
        price = d.get("price", 0)
        change_pct = d.get("change_pct", 0)
        volume = d.get("volume", 0)
        avg_volume = d.get("avg_volume", 1)
        state = d.get("state", "NONE")

        if should_alert(symbol, price, change_pct, volume, avg_volume):
            message = (
                f"#{symbol}\n"
                f"Price: ${round(price, 2)} • {round(change_pct, 2)}%\n\n"
                f"🔥 {state}\n\n"
                f"Volume: {volume}"
            )

            print(f"ALERT: {symbol} → {state}")
            send_alert(message)

# =========================
# 🚀 RUN LOOP
# =========================
def run():
    print("BOT STARTED...")
    while True:
        process_market()
        time.sleep(CHECK_INTERVAL)

# =========================
# ▶️ ENTRY POINT
# =========================

if __name__ == "__main__":
    run()
