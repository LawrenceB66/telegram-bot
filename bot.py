import requests
import time
import os

# ENV
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# ✅ EXPANDED TICKER SET (PHASE 2 — CONTROLLED PRODUCTION)
TICKERS = [
    "AMC","GME","CVNA","UPST","WOK",
    "NVDA","TSLA","AAPL","META",
    "SOFI","PLTR","LCID","RIVN",
    "MARA","RIOT","COIN",
    "SPY","QQQ",
    "AFRM","AI","SMCI","HOOD",
    "DKNG","C3AI","BBAI"
]

# TRACKING MEMORY
last_prices = {}

def send_telegram(message):
    try:
        requests.post(BASE_URL, data={
            "chat_id": CHANNEL_ID,
            "text": message
        })
    except Exception as e:
        print("Telegram Error:", e)

def get_price(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        data = requests.get(url).json()
        return data.get("c")
    except:
        return None

def check_velocity(symbol, price):
    if symbol not in last_prices:
        last_prices[symbol] = price
        return

    prev = last_prices[symbol]

    if prev == 0 or price is None:
        return

    change_pct = ((price - prev) / prev) * 100

    # ⚡️ BULL VELOCITY (tightened)
    if change_pct >= 4:
        send_telegram(
            f"${symbol}\n"
            f"Price {price:.2f} • +{change_pct:.2f}%\n\n"
            f"⚡️ VELOCITY"
        )

    # 🩸 BEAR VELOCITY / BLEEDING
    elif change_pct <= -4:
        send_telegram(
            f"${symbol}\n"
            f"Price {price:.2f} • {change_pct:.2f}%\n\n"
            f"🩸 BLEEDING"
        )

    last_prices[symbol] = price

def run():
    print("🔥 IAL ENGINE — PHASE 2 ACTIVE")
    print("⚡️ Velocity + 🩸 Bleeding Enabled")

    while True:
        for symbol in TICKERS:
            price = get_price(symbol)
            if price:
                check_velocity(symbol, price)

        time.sleep(30)

if __name__ == "__main__":
    run()
