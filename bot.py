import os
import time
import requests

# =========================
# ENV
# =========================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    print("❌ Missing TOKEN or CHAT_ID")
    exit()

print("✅ ENV LOADED")
print("🚀 BOOTING BOT...")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# =========================
# SETTINGS
# =========================
TICKERS = ["AMC", "CVNA", "UPST"]
POLL_INTERVAL = 30
MIN_ALERT_MOVE = 0.5

# =========================
# STATE
# =========================
last_prices = {}
last_signals = {}

# =========================
# SAFE REQUEST
# =========================
def safe_request(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json()
    except Exception as e:
        print(f"⚠️ Request error: {e}")
        return None

# =========================
# DATA (FIXED — NO CRASH)
# =========================
def get_price(ticker):
    url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey=demo"
    data = safe_request(url)

    # ✅ VALID RESPONSE
    if isinstance(data, list) and len(data) > 0:
        return data[0].get("price")

    # ❌ BAD RESPONSE (DO NOT CRASH)
    print(f"⚠️ Bad data for {ticker}: {data}")
    return None

# =========================
# TELEGRAM
# =========================
def send_alert(message):
    params = {
        "chat_id": CHAT_ID,
        "text": message
    }
    safe_request(BASE_URL, params)

# =========================
# SIGNAL LOGIC (BASELINE)
# =========================
def classify_signal(pct_change):
    if pct_change >= 2:
        return "🚀 Breakout"
    elif pct_change >= 1:
        return "🔥 Pressure Cooker"
    elif pct_change >= 0.5:
        return "💣 Ticking Time Bomb"
    elif pct_change <= -2:
        return "🩸 Cascade"
    elif pct_change <= -1:
        return "💥 Sell Pressure"
    elif pct_change <= -0.5:
        return "⚠️ Breakdown"
    else:
        return None

# =========================
# FORMAT MESSAGE
# =========================
def format_message(ticker, price, pct_change, signal):
    return (
        f"${ticker}\n"
        f"Price: {price:.2f}\n"
        f"Move: {pct_change:.2f}%\n\n"
        f"{signal}"
    )

# =========================
# PROCESS TICKER
# =========================
def process_ticker(ticker):
    price = get_price(ticker)

    if price is None:
        print(f"⚠️ No data for {ticker}")
        return

    if ticker not in last_prices:
        last_prices[ticker] = price
        print(f"{ticker} initialized @ {price}")
        return

    prev_price = last_prices[ticker]
    pct_change = ((price - prev_price) / prev_price) * 100

    signal = classify_signal(pct_change)

    if signal and abs(pct_change) >= MIN_ALERT_MOVE:

        last_signal = last_signals.get(ticker)

        if signal != last_signal:
            message = format_message(ticker, price, pct_change, signal)
            send_alert(message)

            print(f"📡 ALERT SENT: {ticker} {signal}")
            last_signals[ticker] = signal
        else:
            print(f"{ticker} duplicate ignored")

    else:
        print(f"{ticker} move ignored ({pct_change:.2f}%)")

    last_prices[ticker] = price

# =========================
# MAIN LOOP
# =========================
def run():
    while True:
        print("\n🔁 New cycle...\n")

        for ticker in TICKERS:
            process_ticker(ticker)

        print("\n😴 Sleeping...\n")
        time.sleep(POLL_INTERVAL)

# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    run()
