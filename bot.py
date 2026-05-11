import requests
import time
import os

# =========================
# ENV VARIABLES
# =========================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FMP_API_KEY = os.getenv("FMP_API_KEY")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# =========================
# SETTINGS
# =========================
symbols = ["AMC", "GME", "CVNA", "UPST"]

MOVE_THRESHOLD = 0.5     # % move to trigger signal
STRONG_MOVE = 1.5       # stronger tier
EVAL_DELAY = 300        # seconds (5 min)

# =========================
# STATE
# =========================
last_prices = {}
signal_log = []

# =========================
# SAFE REQUEST
# =========================
def safe_request(url):
    try:
        return requests.get(url, timeout=10).json()
    except Exception as e:
        print(f"Request error: {e}")
        return None

# =========================
# GET PRICE (FMP)
# =========================
def get_price(symbol):
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={FMP_API_KEY}"
    data = safe_request(url)

    if not data:
        return None

    return data[0]["price"]

# =========================
# TELEGRAM SEND
# =========================
def send_telegram(msg):
    try:
        requests.get(BASE_URL, params={
            "chat_id": CHAT_ID,
            "text": msg
        })
    except Exception as e:
        print(f"Telegram error: {e}")

# =========================
# SIGNAL ENGINE
# =========================
def detect_signal(symbol, price, move):

    # UPSIDE TIERS
    if move >= STRONG_MOVE:
        return "🔥 Ticking Time Bomb"
    elif move >= MOVE_THRESHOLD:
        return "🚀 Breakout"

    # DOWNSIDE TIERS
    if move <= -STRONG_MOVE:
        return "🩸 Cascade"
    elif move <= -MOVE_THRESHOLD:
        return "⚠️ Breakdown"

    return None

# =========================
# LOG SIGNAL
# =========================
def log_signal(symbol, signal_type, price):
    signal_log.append({
        "symbol": symbol,
        "type": signal_type,
        "entry_price": price,
        "timestamp": time.time(),
        "checked": False
    })

# =========================
# EVALUATE SIGNALS
# =========================
def evaluate_signals():
    for s in signal_log:

        if s["checked"]:
            continue

        if time.time() - s["timestamp"] < EVAL_DELAY:
            continue

        current_price = get_price(s["symbol"])
        if current_price is None:
            continue

        move = ((current_price - s["entry_price"]) / s["entry_price"]) * 100

        # Evaluate outcome
        if "Breakdown" in s["type"] or "Cascade" in s["type"]:
            result = "WIN" if move < -1 else "LOSS"
        elif "Breakout" in s["type"] or "Time Bomb" in s["type"]:
            result = "WIN" if move > 1 else "LOSS"
        else:
            result = "NEUTRAL"

        print(f"{s['symbol']} {s['type']} → {result} ({move:.2f}%)")

        s["checked"] = True

# =========================
# MAIN LOOP
# =========================
def run():

    print("🔥 FINAL CONTROLLED VERSION + DIRECTIONAL TIERS 🔥")

    while True:

        print("New cycle...")

        for symbol in symbols:

            price = get_price(symbol)

            if price is None:
                continue

            # Initialize
            if symbol not in last_prices:
                last_prices[symbol] = price
                print(f"{symbol} initialized at {price}")
                continue

            # Calculate move
            move = ((price - last_prices[symbol]) / last_prices[symbol]) * 100

            signal = detect_signal(symbol, price, move)

            if signal:
                msg = (
                    f"🎲 {symbol}\n"
                    f"Price: {price:.2f}\n"
                    f"Move: {move:.2f}%\n\n"
                    f"{signal}"
                )

                print(msg)
                send_telegram(msg)
                log_signal(symbol, signal, price)

            else:
                print(f"{symbol} small move: {move:.2f}% (ignored)")
