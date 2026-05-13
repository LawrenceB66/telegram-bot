import os
import time
import requests

# =========================
# 🔐 ENV VARIABLES
# =========================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

# =========================
# ⚙️ SETTINGS
# =========================
TICKERS = ["AMC", "CVNA", "UPST"]
POLL_INTERVAL = 60  # seconds

# Store last price to prevent spam
last_prices = {}

# =========================
# 🌐 SAFE REQUEST
# =========================
def safe_request(url):
    try:
        response = requests.get(url, timeout=10)
        return response.json()
    except Exception as e:
        print(f"⚠️ Request error: {e}")
        return None

# =========================
# 💰 GET PRICE (FINNHUB)
# =========================
def get_price(ticker):
    url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_API_KEY}"
    data = safe_request(url)

    # Finnhub returns: { c: current price }
    if data and "c" in data and data["c"] != 0:
        return data["c"]

    print(f"⚠️ Bad data for {ticker}: {data}")
    return None

# =========================
# 📊 CLASSIFY MOVE (TEMP BASIC)
# =========================
def classify_move(ticker, price):
    global last_prices

    if ticker not in last_prices:
        last_prices[ticker] = price
        return None

    old_price = last_prices[ticker]
    change_pct = ((price - old_price) / old_price) * 100

    last_prices[ticker] = price

    # 🚫 FILTER NOISE
    if abs(change_pct) < 0.5:
        return None

    # 🔺 UPSIDE
    if change_pct >= 1:
        return "💣 Ticking Time Bomb"
    
    # 🔻 DOWNSIDE
    if change_pct <= -1:
        return "⚠️ Breakdown"

    return None

# =========================
# 📤 SEND ALERT
# =========================
def send_alert(ticker, price, signal):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    message = f"""
${ticker}
Price: {round(price, 2)}

{signal}
"""

    try:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": message
        })
        print(f"✅ Sent: {ticker} | {signal}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

# =========================
# 🔄 PROCESS TICKER
# =========================
def process_ticker(ticker):
    price = get_price(ticker)

    if price is None:
        return

    signal = classify_move(ticker, price)

    if signal:
        send_alert(ticker, price, signal)

# =========================
# 🚀 RUN LOOP
# =========================
def run():
    print("🚀 Bot started...")

    while True:
        print("\n🔁 New cycle...\n")

        for ticker in TICKERS:
            process_ticker(ticker)

        print("😴 Sleeping...\n")
        time.sleep(POLL_INTERVAL)

# =========================
# ▶️ ENTRY POINT
# =========================

if __name__ == "__main__":
    run()
