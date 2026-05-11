print("🔥🔥🔥 FINAL CONTROLLED VERSION + DIRECTIONAL TIERS 🔥🔥🔥")

import requests
import time
import os

# -------------------------
# ENV VARIABLES
# -------------------------
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# -------------------------
# WATCHLIST
# -------------------------
symbols = ["AMC", "GME", "CVNA", "UPST"]

# -------------------------
# STATE TRACKING
# -------------------------
last_prices = {}
last_alert_time = {}

COOLDOWN_SECONDS = 900  # 15 min cooldown

# -------------------------
# SAFE REQUEST
# -------------------------
def safe_request(url):
    try:
        response = requests.get(url, timeout=10)
        return response.json()
    except Exception as e:
        print("Error:", e)
        return None

# -------------------------
# GET PRICE
# -------------------------
def get_price(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
    data = safe_request(url)
    if data and "c" in data:
        return data["c"]
    return None

# -------------------------
# SEND TELEGRAM MESSAGE
# -------------------------
def send_message(text):
    requests.post(BASE_URL, data={"chat_id": CHAT_ID, "text": text})

# -------------------------
# CLASSIFY MOVE (DIRECTIONAL TIERS)
# -------------------------
def classify_move(change_pct):
    # UPSIDE
    if change_pct >= 5:
        return "🔥 Ticking Time Bomb"
    elif change_pct >= 2:
        return "💣 Pressure Cooker"
    elif change_pct >= 1:
        return "🚀 Breakout"

    # DOWNSIDE
    elif change_pct <= -5:
        return "🩸 Cascade"
    elif change_pct <= -2:
        return "💥 Sell Pressure"
    elif change_pct <= -1:
        return "⚠️ Breakdown"

    return None

# -------------------------
# MAIN LOOP
# -------------------------
while True:
    print("\n📊 New cycle...")

    for symbol in symbols:
        price = get_price(symbol)

        if price is None:
            continue

        # FIRST RUN (INITIALIZE)
        if symbol not in last_prices:
            last_prices[symbol] = price
            print(f"{symbol} initialized at {price}")
            continue

        old_price = last_prices[symbol]
        change_pct = ((price - old_price) / old_price) * 100

        # FILTER SMALL MOVES
        if abs(change_pct) < 1:
            print(f"{symbol} small move: {round(change_pct,2)}% (ignored)")
            last_prices[symbol] = price
            continue

        # COOLDOWN CHECK
        now = time.time()
        if symbol in last_alert_time:
            elapsed = now - last_alert_time[symbol]
            if elapsed < COOLDOWN_SECONDS:
                print(f"{symbol} cooldown active ({int(elapsed)}s) — skipped")
                last_prices[symbol] = price
                continue

        # CLASSIFY
        tier = classify_move(change_pct)
        if not tier:
            last_prices[symbol] = price
            continue

        # FORMAT MESSAGE
        direction_emoji = "📈" if change_pct > 0 else "📉"

        message = (
            f"🎲 ${symbol}\n"
            f"Price: {round(price,2)}\n"
            f"Move: {round(change_pct,2)}% {direction_emoji}\n\n"
            f"{tier}"
        )

        # SEND
        send_message(message)
        print(f"ALERT: {symbol} {round(change_pct,2)}% → {tier}")

        # UPDATE STATE
        last_prices[symbol] = price
        last_alert_time[symbol] = now

    print("😴 Sleeping...")
    time.sleep(60)
