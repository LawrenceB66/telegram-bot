import time
import requests

# =========================
# CONFIG
# =========================

TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

VELOCITY_THRESHOLD = 5
COOLDOWN_SECONDS = 300

TICKERS = [
    "AMC","GME","CVNA","UPST","MARA","RIOT","PLTR","SOFI","LCID","NKLA",
    "BB","NIO","XPEV","RIVN","HOOD","COIN","AFRM","DKNG","AI","MULN",
    "SNDL","TLRY","FUBO","OPEN","QS"
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
        requests.post(url, data=data)
    except:
        print("Telegram send failed")

# =========================
# PRICE FETCH (FINNHUB)
# =========================

FINNHUB_API_KEY = "YOUR_FINNHUB_API_KEY"

def get_price(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        response = requests.get(url).json()
        return response.get("c")  # current price
    except:
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

    if old_price == 0:
        return

    change_pct = ((price - old_price) / old_price) * 100

    # -------------------------
    # COOLDOWN
    # -------------------------
    if symbol in last_alert_time:
        if current_time - last_alert_time[symbol] < COOLDOWN_SECONDS:
            last_prices[symbol] = price
            return

    # -------------------------
    # ⚡️ VELOCITY (UP)
    # -------------------------
    if change_pct >= VELOCITY_THRESHOLD:
        send_telegram(
            f"${symbol}\n\n"
            f"Price: {price:.2f} • {change_pct:+.2f}%\n\n"
            f"⚡️ VELOCITY"
        )
        last_alert_time[symbol] = current_time

    # -------------------------
    # 🩸 BLEEDING (DOWN)
    # -------------------------
    elif change_pct <= -VELOCITY_THRESHOLD:
        send_telegram(
            f"${symbol}\n\n"
            f"Price: {price:.2f} • {change_pct:+.2f}%\n\n"
            f"🩸 BLEEDING"
        )
        last_alert_time[symbol] = current_time

    # -------------------------
    # PLACEHOLDER (SI / DTC)
    # -------------------------
    # Will activate later when data is wired
    si = 0
    dtc = 0

    # 🔥 PRESSURE
    if si >= 30 and dtc >= 3:
        send_telegram(
            f"${symbol}\n\n"
            f"Price: {price:.2f} • {change_pct:+.2f}%\n\n"
            f"🔥 PRESSURE\n\n"
            f"DTC: {dtc} • SI: {si}%"
        )
        last_alert_time[symbol] = current_time

    # 💣 TIME BOMB
    if si >= 40 and dtc >= 5:
        send_telegram(
            f"${symbol}\n\n"
            f"Price: {price:.2f} • {change_pct:+.2f}%\n\n"
            f"💣 TIME BOMB\n\n"
            f"DTC: {dtc} • SI: {si}%"
        )
        last_alert_time[symbol] = current_time

    last_prices[symbol] = price

# =========================
# MAIN LOOP
# =========================

def run():
    print("IAL ENGINE — STRUCTURED MODE ACTIVE")
    print("Velocity separated from conviction signals")

    while True:
        for symbol in TICKERS:
            price = get_price(symbol)
            if price:
                check_velocity(symbol, price)

        time.sleep(30)

# =========================
# START
# =========================

if __name__ == "__main__":
    run()
