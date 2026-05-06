import requests
import time
import os

# --- CONFIG ---
TOKEN = os.getenv("TOKEN")
ALPHA_API_KEY = os.getenv("ALPHA_API_KEY")

CHANNEL_ID = -1003667470993
TG_URL = f"https://api.telegram.org/bot{TOKEN}/"

# --- MEMORY (prevents spam) ---
last_prices = {}

# --- SAFE REQUEST ---
def safe_request(url, params=None, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Attempt {attempt+1}: {e}")
            time.sleep(2)
    return None

# --- TELEGRAM SEND ---
def send_alert(text):
    url = TG_URL + "sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text
    }
    safe_request(url, params=payload)

# --- FETCH DATA ---
def fetch_data():
    symbols = ["AMC", "GME", "CVNA", "UPST"]
    results = []

    for symbol in symbols:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_API_KEY}"
        data = safe_request(url)

        if data and "Global Quote" in data:
            quote = data["Global Quote"]

            results.append({
                "symbol": quote.get("01. symbol", "N/A"),
                "price": float(quote.get("05. price", 0)),
                "volume": quote.get("06. volume", "0")
            })

        time.sleep(12)  # Alpha free plan limit

    return results

# --- BUILD MESSAGE ---
def build_message(stock):
    ticker = stock["symbol"]
    price = stock["price"]
    volume = stock["volume"]

    msg = (
        f"${ticker}\n"
        f"Price: ${price:.2f}\n"
        f"Volume: {int(volume):,}"
    )

    return msg

# --- MAIN LOOP ---
def main():
    print("🚀 BOT STARTED")

    while True:
        data = fetch_data()

        if data:
            for stock in data:
                ticker = stock["symbol"]
                price = stock["price"]

                # --- SPAM FILTER ---
                if ticker in last_prices:
                    if price == last_prices[ticker]:
                        continue  # skip if no change

                # --- UPDATE MEMORY ---
                last_prices[ticker] = price

                # --- SEND ALERT ---
                msg = build_message(stock)
                send_alert(msg)

                time.sleep(1)

        time.sleep(30)

# --- RUN ---
if __name__ == "__main__":
    main()
