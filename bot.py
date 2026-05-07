import requests
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

symbols = ["AMC", "GME", "CVNA", "UPST"]

def send_message(message):
    try:
        res = requests.post(BASE_URL, data={
            "chat_id": CHAT_ID,
            "text": message
        })
        print("Telegram response:", res.text)
    except Exception as e:
        print("Send error:", e)

def fetch_data(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        res = requests.get(url)
        data = res.json()

        print(f"🌐 Finnhub RAW ({symbol}):", data)

        price = data.get("c")
        volume = data.get("v")

        if price is not None and volume is not None:
            print(f"✅ Parsed ({symbol}) -> price: {price}, volume: {volume}")
            return price, volume

    except Exception as e:
        print("Fetch error:", e)

    print(f"⚠️ No data returned for {symbol}")
    return None, None


print("🚀 Bot started...")

# TEST MESSAGE (leave this for now)
send_message("🚀 TEST MESSAGE — BOT IS LIVE")

while True:
    print("Running cycle...\n")

    for ticker in symbols:
        price, volume = fetch_data(ticker)

        if price and volume:
            msg = f"${ticker}\nPrice: {price:.2f}\nVolume: {int(volume):,}"
            print("📨 Sending message:\n", msg)
            send_message(msg)
        else:
            print(f"❌ Skipping {ticker} (no data)")

    print("\nCycle complete. Sleeping...\n")
    time.sleep(60)
