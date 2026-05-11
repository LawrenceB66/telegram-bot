import os
import time
import requests

print("🚀 BOOTING BOT...")

# ========================
# ENV VARIABLES
# ========================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FMP_API_KEY = os.getenv("FMP_API_KEY")

print("TOKEN:", TOKEN)
print("CHAT_ID:", CHAT_ID)
print("FMP_API_KEY:", FMP_API_KEY)

if not TOKEN or not CHAT_ID or not FMP_API_KEY:
    print("❌ ENV VARIABLES NOT LOADED — EXITING")
    exit()

BASE_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# ========================
# CONFIG
# ========================
TICKERS = ["GME", "CVNA", "AMC", "UPST"]

POLL_INTERVAL = 30  # seconds

# Thresholds (tune later)
BREAKOUT_THRESHOLD = 1.0
PRESSURE_THRESHOLD = 2.5
BOMB_THRESHOLD = 4.0

BREAKDOWN_THRESHOLD = -1.0
SELL_PRESSURE_THRESHOLD = -2.5
CASCADE_THRESHOLD = -4.0

# ========================
# STATE TRACKING
# ========================
last_prices = {}

# ========================
# HELPERS
# ========================
def safe_request(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"❌ Bad response: {r.status_code}")
            return None
    except Exception as e:
        print("❌ Request error:", e)
        return None


def send_alert(message):
    try:
        requests.post(BASE_URL, json={
            "chat_id": CHAT_ID,
            "text": message
        })
    except Exception as e:
        print("❌ Telegram error:", e)


def get_price(symbol):
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={FMP_API_KEY}"
    data = safe_request(url)

    if data and len(data) > 0:
        return data[0]["price"]
    return None


# ========================
# CLASSIFICATION ENGINE
# ========================
def classify_move(pct):

    # UPSIDE
    if pct >= BOMB_THRESHOLD:
        return "💣 Ticking Time Bomb"
    elif pct >= PRESSURE_THRESHOLD:
        return "🔥 Pressure Cooker"
    elif pct >= BREAKOUT_THRESHOLD:
        return "🚀 Breakout"

    # DOWNSIDE
    elif pct <= CASCADE_THRESHOLD:
        return "🩸 Cascade"
    elif pct <= SELL_PRESSURE_THRESHOLD:
        return "💥 Sell Pressure"
    elif pct <= BREAKDOWN_THRESHOLD:
        return "⚠️ Breakdown"

    return None


# ========================
# MAIN LOOP
# ========================
def run():

    print("✅ BOT RUNNING...\n")

    while True:
        print("🔄 New cycle...\n")

        for ticker in TICKERS:

            price = get_price(ticker)

            if price is None:
                print(f"{ticker} ❌ price fetch failed")
                continue

            if ticker not in last_prices:
                last_prices[ticker] = price
                print(f"{ticker} initialized at {price}")
                continue

            prev = last_prices[ticker]
            pct_change = ((price - prev) / prev) * 100

            print(f"{ticker} move: {round(pct_change, 2)}%")

            signal = classify_move(pct_change)

            if signal:
                message = (
                    f"🎲 $ {ticker}\n"
                    f"Price: {round(price, 2)}\n"
                    f"Move: {round(pct_change, 2)}%\n\n"
                    f"{signal}"
                )

                print(f"⚡ SIGNAL: {signal} on {ticker}")
                send_alert(message)

            else:
                print(f"{ticker} move ignored")

            last_prices[ticker] = price

        print("\n😴 Sleeping...\n")
        time.sleep(POLL_INTERVAL)


# ========================
# ENTRY POINT
# ========================
if name == "__main__":
    run()
