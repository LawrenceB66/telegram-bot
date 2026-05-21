import time
import requests
import os
from collections import deque

# =========================
# CONFIG (ENV VARIABLES)
# =========================

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

# =========================
# STRATEGY SETTINGS (BALANCED)
# =========================

WINDOW_SIZE = 6            # ~3 minutes (6 x 30s loops)
ALERT_THRESHOLD = 2.5      # % move over window
COOLDOWN_SECONDS = 300     # 5 min cooldown

# =========================
# WATCHLIST
# =========================

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

price_history = {symbol: deque(maxlen=WINDOW_SIZE) for symbol in TICKERS}
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
        response = requests.post(url, data=data, timeout=10)
        print(f"Telegram sent: {response.status_code}")
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
# ENGINE LOGIC (BALANCED)
# =========================

def analyze_symbol(symbol, price):
    current_time = time.time()
    history = price_history[symbol]

    history.append(price)

    # Wait until we have full window
    if len(history) < WINDOW_SIZE:
        return

    oldest = history[0]
    newest = history[-1]

    if not oldest or oldest == 0:
        return

    change_pct = ((newest - oldest) / oldest) * 100

    # Cooldown
    if symbol in last_alert_time:
        if current_time - last_alert_time[symbol] < COOLDOWN_SECONDS:
            return

    # =========================
    # ALERTS
    # =========================

    if change_pct >= ALERT_THRESHOLD:
        send_telegram(
            f"${symbol}\n\n"
            f"Price: {newest:.2f} • {change_pct:+.2f}%\n\n"
            f"⚡️ MOMENTUM BUILDING"
        )
        last_alert_time[symbol] = current_time

    elif change_pct <= -ALERT_THRESHOLD:
        send_telegram(
            f"${symbol}\n\n"
            f"Price: {newest:.2f} • {change_pct:+.2f}%\n\n"
            f"🩸 BLEEDING TREND"
        )
        last_alert_time[symbol] = current_time

# =========================
# MAIN LOOP
# =========================

def run():
    print("IAL ENGINE v2 - BALANCED MODE ACTIVE")

    while True:
        try:
            for symbol in TICKERS:
                price = get_price(symbol)
                if price:
                    analyze_symbol(symbol, price)

            time.sleep(30)

        except Exception as e:
            print(f"MAIN LOOP ERROR: {e}")
            time.sleep(10)

# =========================
# START
# =========================

if __name__ == "__main__":
    run()
