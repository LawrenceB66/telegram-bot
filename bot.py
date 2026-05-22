import time
import requests
import os

# =========================
# CONFIG (ENV VARIABLES)
# =========================

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

# 🔥 REFINED THRESHOLDS
MIN_MOVE_PCT = 3.5          # Ignore weak moves
STRONG_MOVE_PCT = 6.0       # Strong momentum
CHECK_INTERVAL = 30         # seconds
COOLDOWN_SECONDS = 300      # 5 min per ticker

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

price_history = {}
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
# CORE ENGINE (REFINED)
# =========================

def check_signal(symbol, price):
    current_time = time.time()

    # Initialize history
    if symbol not in price_history:
        price_history[symbol] = [(current_time, price)]
        return

    # Append latest price
    price_history[symbol].append((current_time, price))

    # Keep only last 5 minutes of data
    price_history[symbol] = [
        (t, p) for (t, p) in price_history[symbol]
        if current_time - t <= 300
    ]

    # Need at least 2 points
    if len(price_history[symbol]) < 2:
        return

    oldest_time, oldest_price = price_history[symbol][0]

    if not oldest_price or oldest_price == 0:
        return

    change_pct = ((price - oldest_price) / oldest_price) * 100
    time_diff = current_time - oldest_time

    # Cooldown check
    if symbol in last_alert_time:
        if current_time - last_alert_time[symbol] < COOLDOWN_SECONDS:
            return

    # =========================
    # SIGNAL LOGIC
    # =========================

    label = None
    emoji = ""

    # ⚡ FAST MOMENTUM (quick move)
    if abs(change_pct) >= MIN_MOVE_PCT and time_diff <= 120:
        label = "MOMENTUM BUILDING"
        emoji = "⚡"

    # 🔥 STRONG PRESSURE (bigger move over time)
    if abs(change_pct) >= STRONG_MOVE_PCT:
        label = "PRESSURE"
        emoji = "🔥"

    if label:
        direction = "+" if change_pct > 0 else ""
        message = (
            f"${symbol}\n\n"
            f"Price: {price:.2f} • {direction}{change_pct:.2f}%\n\n"
            f"{emoji} {label}"
        )

        send_telegram(message)
        last_alert_time[symbol] = current_time

# =========================
# MAIN LOOP
# =========================

def run():
    print("IAL ENGINE V2 - BALANCED MODE ACTIVE")

    while True:
        try:
            for symbol in TICKERS:
                price = get_price(symbol)
                if price:
                    check_signal(symbol, price)

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print(f"MAIN LOOP ERROR: {e}")
            time.sleep(10)


# =========================
# START
# =========================

if __name__ == "__main__":
    run()
