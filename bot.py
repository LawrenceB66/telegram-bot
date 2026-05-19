import requests
import time
import os

# ENV VARIABLES
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# TICKERS (PHASE 2 — CONTROLLED SET)
TICKERS = [
    "AMC","GME","CVNA","UPST","WOK",
    "NVDA","TSLA","AAPL","META",
    "SOFI","PLTR","LCID","RIVN",
    "MARA","RIOT","COIN",
    "SPY","QQQ",
    "AFRM","AI","SMCI","HOOD",
    "DKNG","C3AI","BBAI"
]

# MEMORY
last_prices = {}
last_alert_time = {}

# COOLDOWN (SECONDS)
COOLDOWN = 300  # 5 minutes

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
        response = requests.get(url)
        data = response.json()
        return data.get("c")
    except Exception as e:
        print(f"Price Fetch Error ({symbol}):", e)
        return None

def check_velocity(symbol, price):
    current_time = time.time()

    if symbol not in last_prices:
        last_prices[symbol] = price
        return

    prev = last_prices[symbol]

    if prev == 0 or price is None:
        return

    change_pct = ((price - prev) / prev) * 100

    # COOLDOWN CHECK
    if symbol in last_alert_time:
        if current_time - last_alert_time[symbol] < COOLDOWN:
            last_prices[symbol] = price
            return

    # BULL VELOCITY
    if change_pct >= 4:
        send_telegram(
            f"${symbol}\n"
            f"Price {price:.2f} • +{change_pct:.2f}%\n\n"
            f"VELOCITY"
        )
        last_alert_time[symbol] = current_time

    # BEAR VELOCITY (BLEEDING)
    elif change_pct <= -4:
        send_telegram(
            f"${symbol}\n"
            f"Price {price:.2f} • {change_pct:.2f}%\n\n"
            f"BLEEDING"
        )
        last_alert_time[symbol] = current_time

    last_prices[symbol] = price

def run():
    print("IAL ENGINE — PHASE 2 ACTIVE")
    print("Velocity + Bleeding + Cooldown")

    while True:
        for symbol in TICKERS:
            price = get_price(symbol)
            if price:
                check_velocity(symbol, price)

        time.sleep(30)


if __name__ == "__main__":
    run()
