import requests
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

TICKERS = ["AMC", "CVNA", "UPST", "GME", "WOK"]

last_alert = {}

VELOCITY_THRESHOLD = 0.04
VOLUME_MULTIPLIER = 1.75

def send_alert(message):
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        requests.post(BASE_URL, json=payload, timeout=5)
    except:
        pass

def get_quote(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
    try:
        return requests.get(url, timeout=5).json()
    except:
        return None

def get_candles(symbol):
    now = int(time.time())
    past = now - (60 * 30)  # last 30 mins

    url = f"https://finnhub.io/api/v1/stock/candle?symbol={symbol}&resolution=1&from={past}&to={now}&token={FINNHUB_API_KEY}"

    try:
        data = requests.get(url, timeout=5).json()
        if data.get("s") != "ok":
            return None
        return data
    except:
        return None

def should_alert(ticker):
    now = time.time()
    if ticker not in last_alert or now - last_alert[ticker] > 300:
        last_alert[ticker] = now
        return True
    return False

def analyze_velocity(symbol):
    quote = get_quote(symbol)
    candles = get_candles(symbol)

    if not quote or not candles:
        return

    current_price = quote.get("c")
    prev_close = quote.get("pc")

    if not current_price or not prev_close:
        return

    price_change = (current_price - prev_close) / prev_close

    volumes = candles.get("v", [])
    if len(volumes) < 5:
        return

    avg_volume = sum(volumes[:-1]) / (len(volumes) - 1)
    current_volume = volumes[-1]

    if avg_volume == 0:
        return

    volume_spike = current_volume / avg_volume

    if price_change >= VELOCITY_THRESHOLD and volume_spike >= VOLUME_MULTIPLIER:
        if should_alert(symbol):
            msg = (
                f"${symbol}\n"
                f"Price: {round(current_price, 2)} • {round(price_change * 100, 2)}%\n\n"
                f"⚡️ Velocity Spike\n\n"
                f"Volume: {round(volume_spike, 2)}x avg"
            )
            send_alert(msg)

    # BLEEDING LOGIC (early version)
    highs = candles.get("h", [])
    closes = candles.get("c", [])

    if len(highs) >= 5:
        recent_high = max(highs[:-2])
        last_high = highs[-1]

        if last_high < recent_high and price_change < 0:
            if should_alert(symbol):
                msg = (
                    f"${symbol}\n"
                    f"Price: {round(current_price, 2)} • {round(price_change * 100, 2)}%\n\n"
                    f"🩸 Bleeding / Reversal\n\n"
                    f"Lower high detected"
                )
                send_alert(msg)

def run():
    print("🚀 IAL ENGINE LIVE")

    while True:
        for ticker in TICKERS:
            analyze_velocity(ticker)
        time.sleep(20)

if __name__ == "__main__":
    run()
