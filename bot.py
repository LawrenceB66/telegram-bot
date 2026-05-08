print("🔥🔥🔥 FINAL CONTROLLED VERSION 🔥🔥🔥")

import requests
import time
import os

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
# STATE MEMORY (in-session)
# =========================
last_prices = {}

# =========================
# TELEGRAM SEND
# =========================
def send_message(message):
    try:
        requests.post(BASE_URL, data={
            "chat_id": CHAT_ID,
            "text": message
        })
    except Exception as e:
        print("Telegram error:", e)

# =========================
# GET PRICE (FINNHUB)
# =========================
def get_price(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        res = requests.get(url).json()
        return res.get("c")  # current price
    except:
        return None

# =========================
# MAIN LOOP
# =========================
while True:
    print("\n🔄 New cycle...")

    for ticker in symbols:
        price = get_price(ticker)

        if price is None:
            print(f"{ticker} price fetch failed")
            continue

        # FIRST TIME SEEING TICKER
        if ticker not in last_prices:
            last_prices[ticker] = price
            print(f"{ticker} initialized at {price}")
            continue

        last_price = last_prices[ticker]

        # NO CHANGE
        if price == last_price:
            print(f"{ticker} no change")
            continue

        # % CHANGE CALC
        percent_change = ((price - last_price) / last_price) * 100

        # ONLY TRIGGER IF >= 1% MOVE
        if abs(percent_change) >= 1:

            msg = (
                f"${ticker}\n"
                f"Price: {price:.2f}\n"
                f"Move: {percent_change:.2f}%"
            )

            send_message(msg)

            print(f"{ticker} moved: {last_price} → {price} ({percent_change:.2f}%)")

            # UPDATE STATE AFTER ALERT
            last_prices[ticker] = price

        else:
            print(f"{ticker} small move: {percent_change:.2f}% (ignored)")

    print("😴 Sleeping...\n")
    time.sleep(30)
