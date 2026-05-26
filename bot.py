import requests
import time
import os

# =========================
# ENV VARIABLES (Railway)
# =========================
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

TG_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# =========================
# WATCHLIST (EDITABLE)
# =========================
WATCHLIST = ["AMC", "GME", "CVNA", "UPST"]

# =========================
# SAFE REQUEST FUNCTION
# =========================
def safe_request(url):
    try:
        response = requests.get(url, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Request failed: {e}")
        return None

# =========================
# FETCH MARKET DATA
# =========================
def get_price_data(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
    data = safe_request(url)

    if not data or "c" not in data:
        return None

    return {
        "price": data["c"],
        "change_pct": data["dp"]
    }

# =========================
# CONDITION CHECK (FOUNDATION)
# =========================
def check_conditions(symbol, data):
    """
    TEMP LOGIC:
    Trigger alert if % change > 3%
    (We replace this later with real pressure logic)
    """

    if abs(data["change_pct"]) >= 3:
        return True

    return False

# =========================
# FORMAT ALERT MESSAGE
# =========================
def format_alert(symbol, data):
    price = round(data["price"], 2)
    change = round(data["change_pct"], 2)

    direction = "🔥" if change > 0 else "📉"

    message = (
        f"${symbol}\n"
        f"Price: ${price} • {change}%\n\n"
        f"{direction} Momentum Alert\n\n"
        f"Velocity: High"
    )

    return message

# =========================
# SEND TELEGRAM ALERT
# =========================
def send_alert(message):
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message
    }

    try:
        requests.post(TG_URL, json=payload)
    except Exception as e:
        print(f"Telegram send failed: {e}")

# =========================
# MAIN LOOP
# =========================
def run_bot():
    print("ALERT ENGINE ACTIVE")

    while True:
        for symbol in WATCHLIST:
            data = get_price_data(symbol)

            if not data:
                continue

            if check_conditions(symbol, data):
                message = format_alert(symbol, data)
                send_alert(message)
                print(f"ALERT SENT: {symbol}")

        time.sleep(60)  # runs every 60 seconds


# =========================
# START BOT
# =========================
if __name__ == "__main__":
    run_bot()
