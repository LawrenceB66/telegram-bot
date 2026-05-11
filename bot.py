print("🔥🔥🔥 FINAL CONTROLLED VERSION + DIRECTIONAL TIERS 🔥🔥🔥")

import requests
import time
import os

# =========================
# ENV VARIABLES
# =========================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# =========================
# WATCHLIST
# =========================
symbols = ["AMC", "GME", "CVNA", "UPST"]

# =========================
# STATE STORAGE
# =========================
last_prices = {}
last_alert_time = {}

COOLDOWN_SECONDS = 900  # 15 minutes

# =========================
# SAFE REQUEST
# =========================
def safe_request(url):
    try:
        return requests.get(url, timeout=10).json()
    except Exception as e:
        print(f"Error: {e}")
        return None

# =========================
# GET PRICE (Finnhub)
# =========================
def get_price(symbol):
    api_key = os.getenv("FINNHUB_API_KEY")
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"

    data = safe_request(url)

    if data and "c" in data:
        return float(data["c"])

    return None

# =========================
# SEND TELEGRAM MESSAGE
# =========================
def send_alert(message):
    url = f"{BASE_URL}?chat_id={CHAT_ID}&text={message}"
    safe_request(url)

# =========================
# FORMAT MESSAGE
# =========================
def format_message(symbol, price, change, tier):
    return (
        f"🎲 ${symbol}\n"
        f"Price: {round(price, 2)}\n"
        f"Move: {round(change, 2)}%\n\n"
        f"{tier}"
    )

# =========================
# MAIN LOOP
# =========================
while True:
    print("📊 New cycle...")

    for symbol in symbols:
        price = get_price(symbol)

        if price is None:
            print(f"{symbol} price fetch failed")
            continue

        # Initialize
        if symbol not in last_prices:
            last_prices[symbol] = price
            print(f"{symbol} initialized at {price}")
            continue

        last_price = last_prices[symbol]
        change = ((price - last_price) / last_price) * 100

        print(f"{symbol} change: {round(change,2)}%")

        # =========================
        # FILTER SMALL MOVES
        # =========================
        if abs(change) < 1:
            print(f"{symbol} small move: {round(change,2)}% (ignored)")
            continue

        # =========================
        # COOLDOWN CHECK
        # =========================
        now = time.time()

        if symbol in last_alert_time:
            if now - last_alert_time[symbol] < COOLDOWN_SECONDS:
                print(f"{symbol} cooldown active (blocked)")
                continue

        # =========================
        # TIER LOGIC
        # =========================
        tier = None

        # UPSIDE
        if change >= 1 and change < 2:
            tier = "🚀 Breakout"

        elif change >= 2 and change < 5:
            tier = "💣 Pressure Cooker"

        elif change >= 5:
            tier = "🔥 Ticking Time Bomb"

        # DOWNSIDE
        elif change <= -1 and change > -2.5:
            tier = "⚠️ Breakdown"

        elif change <= -2.5 and change > -5:
            tier = "💥 Sell Pressure"

        elif change <= -5:
            tier = "🩸 Cascade"

        # =========================
        # SEND ALERT
        # =========================
        if tier:
            message = format_message(symbol, price, change, tier)
            send_alert(message)

            print(f"ALERT SENT: {symbol} {tier}")

            last_alert_time[symbol] = now
            last_prices[symbol] = price

    print("😴 Sleeping...\n")
    time.sleep(60)
