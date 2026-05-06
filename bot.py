import requests
import time
import os

# --- CONFIG ---
TOKEN = os.getenv("TOKEN")
FMP_API_KEY = os.getenv("FMP_API_KEY")

CHANNEL_ID = -1003667470993
TG_URL = f"https://api.telegram.org/bot{TOKEN}/"

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

# --- FETCH REAL DATA (FMP - SAFE FOR FREE PLAN) ---
def fetch_data():
    symbols = ["AMC", "GME", "BBBY", "CVNA", "UPST"]
    results = []

    for symbol in symbols:
        url = f"https://financialmodelingprep.com/api/v3/stock/list?apikey={FMP_API_KEY}"
        data = safe_request(url)

        if data and isinstance(data, list):
            results.extend(data)

        time.sleep(1)  # prevent rate limit

    return results

# --- BUILD MESSAGE ---
def build_message(stock):
    ticker = stock.get("symbol", "N/A")
    price = stock.get("price", 0)
    volume = stock.get("volume", 0)

    msg = (
        f"${ticker}\n"
        f"Price: {price}\n"
        f"Volume: {volume}"
    )
    return msg

# --- MAIN LOOP ---
def main():
    print("🚀 BOT STARTED")

    while True:
        data = fetch_data()

        if data:
            for stock in data:
                msg = build_message(stock)
                send_alert(msg)
                time.sleep(1)  # prevent spam burst

        time.sleep(30)  # refresh loop

# --- RUN ---
if __name__ == "__main__":
    main()
