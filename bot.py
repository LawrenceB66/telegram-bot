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
MIN_MOVE_PCT = 3.5
STRONG_MOVE_PCT = 6.0
CHECK_INTERVAL = 30
COOLDOWN_SECONDS = 300

TICKERS = [
    "WOK","MULN","SINT","FFIE","NKLA","SNDL","TLRY","FUBO","OPEN","QS",
    "AMC","GME","CVNA","UPST","SOFI","HOOD","AFRM","DKNG", "MARA",
    "RIOT","COIN", "AI","PLTR", "LCID","RIVN","NIO","XPEV" , "BB","BYND",
    "CLOV","BBBYQ","SPCE", "IONQ","SOUN","BBAI","SMCI","TEM", "ACHR","JOBY",
    "HIMS","RDDT","ARM", "ASTS","RKLB","ENVX","CHPT","GRAB", "SNAP","PINS","SHOP"
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
        print(f"TELEGRAM SEND STATUS: {response.status_code}", flush=True)

        if response.status_code != 200:
            print(f"TELEGRAM RESPONSE: {response.text}", flush=True)

    except Exception as e:
        print(f"TELEGRAM ERROR: {e}", flush=True)

# =========================
# PRICE FETCH
# =========================

def get_price(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()

        price = data.get("c")

        print(f"SCAN: {symbol} | RAW PRICE: {price}", flush=True)

        if price is None or price == 0:
            print(f"NO VALID PRICE: {symbol} | RESPONSE: {data}", flush=True)
            return None

        return price

    except Exception as e:
        print(f"PRICE FETCH ERROR: {symbol} | {e}", flush=True)
        return None

# =========================
# CORE ENGINE
# =========================

def check_signal(symbol, price):
    current_time = time.time()

    if symbol not in price_history:
        price_history[symbol] = [(current_time, price)]
        print(f"INIT HISTORY: {symbol} | PRICE: {price:.2f}", flush=True)
        return

    price_history[symbol].append((current_time, price))

    price_history[symbol] = [
        (t, p) for (t, p) in price_history[symbol]
        if current_time - t <= 300
    ]

    if len(price_history[symbol]) < 2:
        print(f"WAITING FOR DATA: {symbol}", flush=True)
        return

    oldest_time, oldest_price = price_history[symbol][0]

    if not oldest_price or oldest_price == 0:
        print(f"BAD OLDEST PRICE: {symbol}", flush=True)
        return

    change_pct = ((price - oldest_price) / oldest_price) * 100
    time_diff = current_time - oldest_time

    print(
        f"EVAL: {symbol} | PRICE: {price:.2f} | CHANGE: {change_pct:.2f}% | WINDOW: {int(time_diff)}s",
        flush=True
    )

    if symbol in last_alert_time:
        cooldown_remaining = COOLDOWN_SECONDS - (current_time - last_alert_time[symbol])
        if cooldown_remaining > 0:
            print(f"COOLDOWN: {symbol} | {int(cooldown_remaining)}s remaining", flush=True)
            return

    label = None
    emoji = ""

    if abs(change_pct) >= MIN_MOVE_PCT and time_diff <= 120:
        label = "MOMENTUM BUILDING"
        emoji = "⚡"

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

        print(f"SIGNAL TRIGGERED: {symbol} | {label}", flush=True)
        send_telegram(message)
        last_alert_time[symbol] = current_time

    else:
        print(f"NO SIGNAL: {symbol}", flush=True)

# =========================
# MAIN LOOP
# =========================

def run():
    print("IAL ENGINE V2 - BALANCED MODE ACTIVE", flush=True)

    print(f"TOKEN LOADED: {bool(TOKEN)}", flush=True)
    print(f"CHAT_ID LOADED: {bool(CHAT_ID)}", flush=True)
    print(f"FINNHUB KEY LOADED: {bool(FINNHUB_API_KEY)}", flush=True)

    cycle = 1

    while True:
        try:
            print(f"===== SCAN CYCLE {cycle} START =====", flush=True)

            for symbol in TICKERS:
                price = get_price(symbol)

                if price:
                    check_signal(symbol, price)

                time.sleep(1)

            print(f"===== SCAN CYCLE {cycle} COMPLETE =====", flush=True)
            print(f"SLEEPING {CHECK_INTERVAL} SECONDS", flush=True)

            cycle += 1
            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print(f"MAIN LOOP ERROR: {e}", flush=True)
            time.sleep(10)

# =========================
# START
# =========================

if __name__ == "__main__":
    run()
