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
        requests.post(BASE_URL, data={
            "chat_id": CHAT_ID,
            "text": message
        })
    except Exception as e:
        print("Send error:", e)

def fetch_data(symbol):
    try:
        url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey=demo"
        res = requests.get(url)
        data = res.json()

        if isinstance(data, list) and len(data) > 0:
            price = data[0].get("price", 0)
            volume = data[0].get("volume", 0)

            return price, volume

    except Exception as e:
        print("Fetch error:", e)

    return None, None


# 🔥 MAIN LOOP (THIS WAS MISSING)
print("Bot started...")

while True:
    print("Running cycle...")

    for ticker in symbols:
        price, volume = fetch_data(ticker)

        if price and volume:
            # Clean formatting (no ugly decimals)
            price_fmt = f"{price:.2f}"
            volume_fmt = f"{int(volume):,}"

            msg = f"${ticker}\nPrice: {price_fmt}\nVolume: {volume_fmt}"

            print(msg)
            send_message(msg)

    print("Cycle complete. Sleeping...\n")
    time.sleep(60)
