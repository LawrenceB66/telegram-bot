import os
import time
import requests

# =========================
# ENV VARIABLES
# =========================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

if not TOKEN or not CHAT_ID or not FINNHUB_API_KEY:
    print("❌ ENV VARIABLES NOT LOADED — EXITING")
    exit()

print("🚀 BOOTING BOT...")
print(f"CHAT_ID: {CHAT_ID}")
print(f"FINNHUB_API_KEY: {'LOADED' if FINNHUB_API_KEY else 'None'}")

# =========================
# CONFIG
# =========================
TICKERS = ["GME", "AMC", "CVNA", "UPST"]
POLL_INTERVAL = 30  # seconds

last_prices = {}

# =========================
# TELEGRAM
# =========================
def send_alert(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"❌ Telegram error: {e}")

# =========================
# DATA FETCH (FINNHUB)
# =========================
def get_price(ticker):
    url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_API_KEY}"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            print(f"❌ Bad response: {response.status_code}")
            return None

        data = response.json()

        # Finnhub returns:
        # c = current price
        # h = high
        # l = low
        # o = open
        # pc = previous close

        price = data.get("c")

        if price is None or price == 0:
            print(f"❌ Invalid price for {ticker}")
            return None

        return price

    except Exception as e:
        print(f"❌ Request error: {e}")
        return None

# =========================
# SIGNAL CLASSIFICATION
# =========================
def classify_move(pct_change):
    # UPSIDE
    if pct_change >= 3:
        return "🚀 Breakout"
    elif pct_change >= 2:
        return "🔥 Pressure Cooker"
    elif pct_change >= 1:
        return "💣 Ticking Time Bomb"

    # DOWNSIDE
    elif pct_change <= -3:
        return "🩸 Cascade"
    elif pct_change <= -2:
        return "💥 Sell Pressure"
    elif pct_change <= -1:
        return "⚠️ Breakdown"

    return None

# =========================
# MAIN LOOP
# =========================
def run():
    global last_prices

    while True:
        print("\n📊 New cycle...")

        for ticker in TICKERS:
            price = get_price(ticker)

            if price is None:
                print(f"{ticker} ❌ price fetch failed")
                continue

            if ticker not in last_prices:
                last_prices[ticker] = price
                print(f"{ticker} initialized at {price}")
                continue

            prev_price = last_prices[ticker]
            pct_change = ((price - prev_price) / prev_price) * 100

            print(f"{ticker} change: {pct_change:.2f}%")

            signal = classify_move(pct_change)

            if signal:
                message = (
                    f"${ticker}\n"
                    f"Price: {price:.2f}\n"
                    f"Move: {pct_change:.2f}%\n\n"
                    f"{signal}"
                )

                send_alert(message)
                print(f"📡 ALERT SENT: {ticker} {signal}")

            else:
                print(f"{ticker} move ignored")

            last_prices[ticker] = price

        print("\n😴 Sleeping...\n")
