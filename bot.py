import requests
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# Your watchlist
symbols = ["AMC", "GME", "CVNA", "UPST"]


def send_message(message):
    try:
        res = requests.post(BASE_URL, data={
            "chat_id": CHAT_ID,
            "text": message
        })
        print("📤 Telegram response:", res.text)
    except Exception as e:
        print("❌ Send error:", e)


def fetch_data(symbol):
    try:
        url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey=demo"
        res = requests.get(url)

        # 🔥 SEE EXACT RESPONSE
        print(f"\n🌐 RAW API ({symbol}):", res.text)

        data = res.json()

        if isinstance(data, list) and len(data) > 0:
            stock = data[0]

            price = stock.get("price", None)
            volume = stock.get("volume", None)

            print(f"✅ Parsed ({symbol}) -> price: {price}, volume: {volume}")

            return price, volume

    except Exception as e:
        print(f"❌ Fetch error ({symbol}):", e)

    print(f"⚠️ No data returned for {symbol}")
    return None, None


# 🔥 MAIN LOOP
print("🚀 Bot started...\n")

while True:
    print("🔁 Running cycle...\n")

    for ticker in symbols:
        price, volume = fetch_data(ticker)

        if price is not None and volume is not None:
            price_fmt = f"{price:.2f}"
            volume_fmt = f"{int(volume):,}"

            msg = f"${ticker}\nPrice: {price_fmt}\nVolume: {volume_fmt}"

            print("\n📨 Sending message:")
            print(msg)

            send_message(msg)

        else:
            print(f"⛔ Skipping {ticker} (no data)\n")

    print("⏸️ Cycle complete. Sleeping...\n")
    time.sleep(60)
