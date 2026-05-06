import requests
import time
import os

# --- SAFE REQUEST ---
def safe_request(url, params=None, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=(5, 30))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Attempt {attempt+1}: {e}")
            time.sleep(5)
    return None


# --- CONFIG ---
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = -1003667470993
URL = f"https://api.telegram.org/bot{TOKEN}/"


# --- ALERT SENDER ---
def send_alert(ticker, price, pct, tier, dtc, si, velocity):
    message = (
        f"${ticker}\n"
        f"Price {price} • {pct}%\n\n"
        f"{tier}\n\n"
        f"DTC: {dtc} • SI: {si}%\n"
        f"Velocity: {velocity}"
    )

    safe_request(URL + "sendMessage", {
        "chat_id": CHANNEL_ID,
        "text": message
    })


# --- LIVE PRICE FETCH (Yahoo Finance) ---
def get_live_price(ticker):
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={ticker}"
    data = safe_request(url)

    try:
        result = data["quoteResponse"]["result"][0]
        price = result["regularMarketPrice"]
        pct = result["regularMarketChangePercent"]
        return round(price, 2), round(pct, 2)
    except:
        return None, None


# --- HYBRID DATA ENGINE ---
def get_top5():
    base = [
        {"ticker": "AMC", "tier": "💣 POWDER KEG", "dtc": 6.2, "si": 38, "velocity": -0.004},
        {"ticker": "GME", "tier": "💣 POWDER KEG", "dtc": 3.8, "si": 21, "velocity": -0.012},
        {"ticker": "BBBY", "tier": "🔥 TICKING TIME BOMB", "dtc": 1.9, "si": 47, "velocity": 0.021},
        {"ticker": "CVNA", "tier": "🔥 TICKING TIME BOMB", "dtc": 2.3, "si": 31, "velocity": 0.015},
        {"ticker": "UPST", "tier": "💣 POWDER KEG", "dtc": 5.1, "si": 29, "velocity": -0.008},
    ]

    results = []

    for stock in base:
        price, pct = get_live_price(stock["ticker"])

        if price is None:
            continue

        results.append({
            "ticker": stock["ticker"],
            "price": price,
            "pct": pct,
            "tier": stock["tier"],
            "dtc": stock["dtc"],
            "si": stock["si"],
            "velocity": stock["velocity"]
        })

    return results


# --- STATE ENGINE ---
last_sent = {}

def should_alert(stock):
    ticker = stock["ticker"]

    if ticker not in last_sent:
        last_sent[ticker] = stock
        return True

    prev = last_sent[ticker]

    try:
        price_changed = stock["price"] != prev["price"]
        pct_jump = abs(stock["pct"] - prev["pct"]) >= 0.5
        velocity_shift = abs(stock["velocity"] - prev["velocity"]) >= 0.01
    except:
        return False

    if price_changed or pct_jump or velocity_shift:
        last_sent[ticker] = stock
        return True

    return False


# --- MAIN LOOP ---
while True:
    top5 = get_top5()

    for stock in top5:
        if should_alert(stock):
            send_alert(
                stock["ticker"],
                stock["price"],
                stock["pct"],
                stock["tier"],
                stock["dtc"],
                stock["si"],
                stock["velocity"]
            )
            time.sleep(1)

    time.sleep(30)
