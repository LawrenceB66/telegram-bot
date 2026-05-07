import requests
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Your watchlist
SYMBOLS = ["AMC", "GME", "CVNA", "UPST"]

# Track last sent states (prevents spam)
last_states = {}

# Track previous prices for movement detection
previous_prices = {}

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=data)

def format_price(price):
    return f"{price:.2f}"

def classify(symbol, price, volume):
    prev_price = previous_prices.get(symbol, price)
    price_change = (price - prev_price) / prev_price if prev_price != 0 else 0

    # Basic thresholds (can tune later)
    if abs(price_change) > 0.03:
        return "⚡️ Movers"
    elif abs(price_change) > 0.015:
        return "💣 Time Bomb"
    else:
        return "🔥 Pressure"

def fetch_data():
    results = []

    for symbol in SYMBOLS:
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={os.getenv('ALPHA_API_KEY')}"
            response = requests.get(url)
            data = response.json()

            if "Global Quote" in data:
                quote = data["Global Quote"]

                price = float(quote["05. price"])
                volume = int(quote["06. volume"])

                results.append({
                    "symbol": symbol,
                    "price": price,
                    "volume": volume
                })

        except Exception as e:
            print(f"Error fetching {symbol}: {e}")

    return results

def run():
    while True:
        data = fetch_data()

        for item in data:
            symbol = item["symbol"]
            price = item["price"]
            volume = item["volume"]

            classification = classify(symbol, price, volume)

            # Prevent duplicate spam
            if last_states.get(symbol) == classification:
                continue

            last_states[symbol] = classification
            previous_prices[symbol] = price

            message = (
                f"${symbol}\n\n"
                f"Price: ${format_price(price)}\n"
                f"Volume: {volume:,}\n\n"
                f"{classification}"
            )

            send_telegram(message)

        time.sleep(60)  # 1-minute loop

if __name__ == "__main__":
    run()
