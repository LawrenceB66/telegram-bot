import requests
import time
import os

# --- CONFIG ---
TOKEN = os.getenv("TOKEN")
FMP_API_KEY = os.getenv("FMP_API_KEY")

CHANNEL_ID = -1003667470993
URL = f"https://api.telegram.org/bot{TOKEN}/"

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

# --- TELEGRAM SEND ---
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

# --- REAL DATA (FMP) ---
def get_real_top5():
    url = f"https://financialmodelingprep.com/api/v3/quote/AMC,GME,BBBY,CVNA,UPST?apikey={FMP_API_KEY}"
    data = safe_request(url)

    if not data:
        return []

    results = []

    for stock in data:
        ticker = stock.get("symbol")
        price = round(stock.get("price", 0), 2)
        pct = round(stock.get("changesPercentage", 0), 2)

        # TEMP placeholders until we wire real SI/DTC
        si = 30
        dtc = 3
        velocity = round(pct / 100, 3)

        tier = "🔥 TICKING TIME BOMB" if dtc <= 3 else "💣 POWDER KEG"

        results.append({
            "ticker": ticker,
            "price": price,
            "pct": pct,
            "tier": tier,
            "dtc": dtc,
            "si": si,
            "velocity": velocity
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
        pct_jump = abs(float(stock["pct"]) - float(prev["pct"])) >= 1.0
        velocity_shift = abs(float(stock["velocity"]) - float(prev["velocity"])) >= 0.01
    except:
        return False

    if price_changed or pct_jump or velocity_shift:
        last_sent[ticker] = stock
        return True

    return False

# --- MAIN LOOP ---
while True:
    top5 = get_real_top5()

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
