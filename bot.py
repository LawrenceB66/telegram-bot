print("🔥🔥🔥 FINAL CONTROL LAYER V1 🔥🔥🔥")

import requests
import time
import os

# =========================
# ENV VARIABLES
# =========================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# =========================
# WATCHLIST
# =========================
symbols = ["AMC", "GME", "CVNA", "UPST"]

# =========================
# STATE MEMORY
# =========================
last_prices = {}
last_alert_time = {}

# =========================
# SETTINGS
# =========================
MOVE_THRESHOLD = 1.0      # % move required
COOLDOWN_SECONDS = 900   # 15 min cooldown

# =========================
# SAFE REQUEST
# =========================
def safe_request(url):
    try:
        response = requests.get(url, timeout=10)
        return response.json()
    except Exception as e:
        print(f"ERROR: {e}")
        return None

# =========================
# SEND TELEGRAM MESSAGE
# =========================
def send_message(text):
    try:
        requests.post(BASE_URL, data={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print(f"Send error: {e}")

# =========================
# GET PRICE
# =========================
def get_price(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
    data = safe_request(url)

    if data and "c" in data:
        return float(data["c"])
    return None

# =========================
# MAIN LOOP
# =========================
while True:
    print("📡 New cycle...")

    for ticker in symbols:
        price = get_price(ticker)

        if price is None:
            print(f"{ticker} price fetch failed")
            continue

        # =========================
        # INITIALIZE PRICE
        # =========================
        if ticker not in last_prices:
            last_prices[ticker] = price
            print(f"{ticker} initialized at {price}")
            continue

        last_price = last_prices[ticker]

        # =========================
        # CALCULATE % MOVE
        # =========================
        percent = ((price - last_price) / last_price) * 100

        # =========================
        # IGNORE SMALL MOVES
        # =========================
        if abs(percent) < MOVE_THRESHOLD:
            print(f"{ticker} small move: {percent:.2f}% (ignored)")
            continue

        # =========================
        # COOLDOWN CHECK
        # =========================
        now = time.time()

        if ticker in last_alert_time:
            elapsed = now - last_alert_time[ticker]

            if elapsed < COOLDOWN_SECONDS:
                print(f"{ticker} cooldown active ({int(elapsed)}s)")
                continue

        # =========================
        # TIER LOGIC
        # =========================
        abs_move = abs(percent)

        if abs_move >= 5:
            tier = "🔥 Ticking Time Bomb"
        elif abs_move >= 2:
            tier = "💣 Pressure Cooker"
        else:
            tier = "🚀 Breakout"

        # =========================
        # FORMAT MESSAGE
        # =========================
        direction = "📈" if percent > 0 else "📉"

        msg = (
            f"🎲 ${ticker}\n"
            f"Price: {price:.2f}\n"
            f"Move: {percent:+.2f}% {direction}\n\n"
            f"{tier}"
        )

        # =========================
        # SEND ALERT
        # =========================
        send_message(msg)

        print(f"{ticker} ALERT SENT: {percent:.2f}%")

        # =========================
        # UPDATE STATE
        # =========================
        last_prices[ticker] = price
        last_alert_time[ticker] = now

    print("😴 Sleeping...\n")
    time.sleep(60)
