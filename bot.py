import os
import time
import requests

# =========================
# ENV VARIABLES
# =========================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FMP_API_KEY = os.getenv("FMP_API_KEY")

if not TOKEN or not CHAT_ID or not FMP_API_KEY:
    print("❌ ENV VARIABLES NOT LOADED — EXITING")
    exit()

print("🚀 BOOTING BOT...")
print(f"CHAT_ID: {CHAT_ID}")
print(f"FMP_API_KEY: {'LOADED' if FMP_API_KEY else 'None'}")

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
# DATA FETCH (FMP)
# =========================
def get_price(ticker):
    url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={FMP_API_KEY}"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            print(f"❌ Bad response: {response.status_code}")
            return None

        data = response.json()

        if not data or len(data) == 0:
            print(f"❌ No data for {ticker}")
            return None

        return data[0]["price"]

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
        time.sleep(POLL_INTERVAL)

# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    run()
