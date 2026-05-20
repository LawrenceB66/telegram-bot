import time
import requests
import os

# =========================
# CONFIG (ENV VARIABLES)
# =========================

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

VELOCITY_THRESHOLD = 5
COOLDOWN_SECONDS = 300

TICKERS = [
    "WOK","MULN","SINT","FFIE","NKLA","SNDL","TLRY","FUBO","OPEN","QS",
    "AMC","GME","CVNA","UPST","SOFI","HOOD","AFRM","DKNG",
    "MARA","RIOT","COIN",
    "AI","PLTR",
    "LCID","RIVN","NIO","XPEV"
]

# =========================
# STATE
# =========================

last_prices = {}
last_alert_time = {}

# =========================
# TELEGRAM
# =========================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

# =========================
# PRICE FETCH
# =========================

def get_price(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        response = requests.get(url, timeout=10).json()
        return response.get("c")
    except Exception as e:
        print(f"Price fetch error for {symbol}: {e}")
        return None

# =========================
# CORE ENGINE
# =========================

def check_velocity(symbol, price):
    current_time = time.time()

    if symbol not in last_prices:
        last_prices[symbol] = price
        return

    old_price = last_prices[symbol]

    if not old_price or old_price == 0:
        last_prices[symbol] = price
        return

    change_pct = ((price - old_price) / old_price) * 100

    if symbol in last_alert_time:
        if current_time - last_alert_time[symbol] < COOLDOWN_SECONDS:
            last_prices[symbol] = price
            return

    if change_pct >= VELOCITY_THRESHOLD:
        send_telegram(
            f"${symbol}\n\n"
            f"Price: {price:.2f} • {change_pct:+.2f}%\n\n"
            f"VELOCITY"
        )
        last_alert_time[symbol] = current_time

    elif change_pct <= -VELOCITY_THRESHOLD:
        send_telegram(
            f"${symbol}\n\n"
            f"Price: {price:.2f} • {change_pct:+.2f}%\n\n"
            f"BLEEDING"
        )
        last_alert_time[symbol] = current_time

    last_prices[symbol] = price

# =========================
# MAIN LOOP
# =========================

def run():
    print("IAL ENGINE - CLEAN BASELINE ACTIVE")

    while True:
        try:
            for symbol in TICKERS:
                price = get_price(symbol)
                if price:
                    check_velocity(symbol, price)

            time.sleep(30)

        except Exception as e:
            print(f"MAIN LOOP ERROR: {e}")
            time.sleep(10)

# =========================
# START
# =========================

if __name__ == "__main__":
    run()
