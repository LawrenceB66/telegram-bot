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
        print("Telegram response:", res.text)
    except Exception as e:
        print("Send error:", e)


def fetch_data(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
        res = requests.get(url)
        data = res.json()

        result = data["quoteResponse"]["result"]

        if len(result) > 0:
            stock = result[0]

            price = stock.get("regularMarketPrice", None)
            volume = stock.get("regularMarketVolume", None)

            return price, volume

    except Exception as e:
        print("Fetch error:", e)

    return None, None


# 🔥 MAIN LOOP
print("Bot started...")

while True:
    print("Running cycle...")

    for ticker in symbols:
        price, volume = fetch_data(ticker)

        # 🔍 DEBUG (shows what's happening)
        print(f"{ticker} -> price: {price}, volume: {volume}")

        if price is not None and volume is not None:
            price_fmt = f"{price:.2f}"
            volume_fmt = f"{int(volume):,}"

            msg = f"${ticker}\nPrice: {price_fmt}\nVolume: {volume_fmt}"

            print("Sending message:")
            print(msg)

            send_message(msg)

    print("Cycle complete. Sleeping...\n")
    time.sleep(60)
