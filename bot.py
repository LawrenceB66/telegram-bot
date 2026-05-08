print("🔥🔥🔥 THIS IS THE NEW FINNHUB VERSION 🔥🔥🔥")

import requests
import time
import os

# ENV VARIABLES
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# WATCHLIST
symbols = ["AMC", "GME", "CVNA", "UPST"]

# SEND MESSAGE
def send_message(message):
    try:
        res = requests.post(BASE_URL, data={
            "chat_id": CHAT_ID,
            "text": message
        })
        print("📤 Telegram response:", res.text)
    except Exception as e:
        print("❌ Send error:", e)

# FETCH DATA FROM FINNHUB
def fetch_data(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        res = requests.get(url)
        data = res.json()

        print(f"🌐 Finnhub RAW ({symbol}):", data)

        price = data.get("c")

        if price is not None:
            print(f"✅ Parsed ({symbol}) -> price: {price}")
            return price

    except Exception as e:
        print("❌ Fetch error:", e)

    print(f"⚠️ No data returned for {symbol}")
    return None


print("🚀 Bot started...")

# TEST MESSAGE (CONFIRM BOT WORKS)
send_message("🚀 TEST MESSAGE — BOT IS LIVE")

# MAIN LOOP
while True:
    print("\n🔁 Running cycle...\n")

    for ticker in symbols:
        price = fetch_data(ticker)

        if price is not None:
            msg = f"${ticker}\nPrice: {price:.2f}"
            print("📨 Sending message:\n", msg)
            send_message(msg)
        else:
            print(f"❌ Skipping {ticker} (no data)")

    print("\n✅ Cycle complete. Sleeping...\n")
    time.sleep(60)
