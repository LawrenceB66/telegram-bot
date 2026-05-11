print("🔥🔥🔥 CONTROL LAYER V1 🔥🔥🔥")

import requests
import time
import os

# ==============================
# ENV VARIABLES
# ==============================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# ==============================
# WATCHLIST
# ==============================
symbols = ["AMC", "GME", "CVNA", "UPST"]

# ==============================
# STATE
# ==============================
last_prices = {}
last_alert_time = {}

COOLDOWN_SECONDS = 900  # 15 minutes

# ==============================
# HELPERS
# ==============================
def send_message(text):
    try:
        requests.post(BASE_URL, json={
            "chat_id": CHAT_ID,
            "text": text
        })
    except Exception as e:
        print("Send error:", e)

def get_price(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        r = requests.get(url, timeout=5)
        data = r.json()
        return data.get("c")
    except Exception as e:
        print(f"{symbol} fetch error:", e)
        return None

def get_tier(percent):
    if abs(percent) >= 5:
        return "🔥 Ticking Time Bomb"
    elif abs(percent) >= 2:
        return "💣 Pressure Cooker"
    else:
        return None

# ==============================
# MAIN LOOP
# ==============================
while True:
    print("📊 New cycle...")

    for symbol in symbols:
        price = get_price(symbol)

        if price is None:
            continue

        # First-time initialization
        if symbol not in last_prices:
            last_prices[symbol] = price
            print(f"{symbol} initialized at {price}")
            continue

        last_price = last_prices[symbol]

        if last_price == 0:
            continue

        percent = ((price - last_price) / last_price) * 100

        # Ignore small moves (<1%)
        if abs(percent) < 1:
            print(f"{symbol} small move: {percent:.2f}% (ignored)")
            continue

        # Cooldown check
        now = time.time()
        last_time = last_alert_time.get(symbol, 0)

        if now - last_time < COOLDOWN_SECONDS:
            print(f"{symbol} cooldown active (blocked)")
            continue

        tier = get_tier(percent)

        if tier is None:
            print(f"{symbol} move {percent:.2f}% but no tier")
            continue

        # ==============================
        # MESSAGE FORMAT (PREMIUM)
        # ==============================
        msg = (
            f"🎲 ${symbol}\n"
            f"Price: {price:.2f}\n"
            f"Move: {percent:+.2f}%\n\n"
            f"{tier}"
        )

        send_message(msg)

        print(f"{symbol} ALERT SENT: {percent:.2f}%")

        # Update state
        last_prices[symbol] = price
        last_alert_time[symbol] = now

    print("😴 Sleeping...\n")
    time.sleep(60)
