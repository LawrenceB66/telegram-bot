import requests
import time
import os

print("🚀 STATE ENGINE ACTIVE 🚀")

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

# =========================
# SEND MESSAGE
# =========================
def send_message(message):
    try:
        requests.post(BASE_URL, data={
            "chat_id": CHAT_ID,
            "text": message
        })
    except Exception as e:
        print("Send error:", e)

# =========================
# FETCH PRICE
# =========================
def get_price(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
    try:
        res = requests.get(url).json()
        price = res.get("c")
        return price
    except:
        return None

# =========================
# MAIN LOOP
# =========================
while True:
    print("\n🔁 New cycle...")

    for ticker in symbols:
        price = get_price(ticker)

        if price is None:
            continue

        last_price = last_prices.get(ticker)

        # 🔥 STATE ENGINE LOGIC
        if last_price is None:
            # First time seeing it → store only (no send)
            last_prices[ticker] = price
            print(f"{ticker} initialized at {price}")

        elif price != last_price:
            # Price changed → SEND ALERT
            msg = f"${ticker}\nPrice: {price:.2f}"
            send_message(msg)

            print(f"{ticker} moved: {last_price} → {price}")

            # Update memory
            last_prices[ticker] = price

        else:
            print(f"{ticker} no change")

    print("😴 Sleeping...\n")
    time.sleep(30)
