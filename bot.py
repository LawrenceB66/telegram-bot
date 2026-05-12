import os
import time
import requests

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

TICKERS = ["GME", "AMC", "CVNA", "UPST"]
POLL_INTERVAL = 30  # seconds

# =========================
# VALIDATION
# =========================
if not TOKEN or not CHAT_ID or not FINNHUB_API_KEY:
    print("❌ ENV VARIABLES NOT LOADED - EXITING")
    print(f"TOKEN: {TOKEN}")
    print(f"CHAT_ID: {CHAT_ID}")
    print(f"FINNHUB_API_KEY: {FINNHUB_API_KEY}")
    exit()

print("✅ ENV LOADED")
print("🚀 BOOTING BOT...")

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
        print(f"❌ TELEGRAM ERROR: {e}")

# =========================
# FINNHUB PRICE
# =========================
def get_price(ticker):
    url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_API_KEY}"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()

        if "c" in data and data["c"] != 0:
            return data["c"]
        else:
            print(f"❌ {ticker} bad data: {data}")
            return None

    except Exception as e:
        print(f"❌ {ticker} fetch error: {e}")
        return None

# =========================
# SIGNAL ENGINE
# =========================
last_prices = {}

def process_ticker(ticker):
    price = get_price(ticker)

    if price is None:
        print(f"{ticker} price fetch failed")
        return

    if ticker not in last_prices:
        last_prices[ticker] = price
        print(f"{ticker} initialized at {price}")
        return

    prev = last_prices[ticker]
    pct_change = ((price - prev) / prev) * 100

    signal = None

    # ===== UPSIDE =====
    if pct_change > 2:
        signal = "🚀 Breakout"
    elif pct_change > 1:
        signal = "🔥 Pressure Cooker"
    elif pct_change > 0.5:
        signal = "💣 Ticking Time Bomb"

    # ===== DOWNSIDE =====
    elif pct_change < -2:
        signal = "🩸 Cascade"
    elif pct_change < -1:
        signal = "💥 Sell Pressure"
    elif pct_change < -0.5:
        signal = "⚠️ Breakdown"

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

# =========================
# MAIN LOOP
# =========================
def run():
    while True:
        print("\n🔄 New cycle...\n")

        for ticker in TICKERS:
            process_ticker(ticker)

        print("\nSleeping...\n")
        time.sleep(POLL_INTERVAL)

# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    run()
