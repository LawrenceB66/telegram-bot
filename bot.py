import requests
import time
import os

# =========================
# ENV VARIABLES
# =========================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

TG_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# =========================
# WATCHLIST
# =========================
SYMBOLS = ["AMC", "CVNA", "UPST"]

# =========================
# TELEGRAM FUNCTION
# =========================
def send_telegram_message(message):
    try:
        payload = {
            "chat_id": CHAT_ID,
            "text": message
        }
        response = requests.post(TG_URL, data=payload, timeout=10)
        print("TELEGRAM RESPONSE:", response.text)
    except Exception as e:
        print("TELEGRAM ERROR:", e)

# =========================
# GET STOCK DATA
# =========================
def get_quote(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()
        return data
    except Exception as e:
        print(f"ERROR FETCHING {symbol}:", e)
        return None

# =========================
# MAIN LOOP
# =========================
def run_bot():
    print("BOT STARTED")

    while True:
        for symbol in SYMBOLS:
            data = get_quote(symbol)

            if not data:
                continue

            price = data.get("c")
            prev_close = data.get("pc")

            if not price or not prev_close:
                continue

            change_pct = ((price - prev_close) / prev_close) * 100

            print(f"{symbol} | Price: {price} | Change: {change_pct:.2f}%")

            # =========================
            # TEMP ALERT CONDITION
            # =========================
            if abs(change_pct) > 2:
                message = (
                    f"{symbol}\n"
                    f"Price: {price:.2f}\n"
                    f"Change: {change_pct:.2f}%\n\n"
                    f"TEST ALERT 🚨 {time.time()}"
                )

                send_telegram_message(message)
                print(f"ALERT SENT: {symbol}")

        time.sleep(60)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    run_bot()
