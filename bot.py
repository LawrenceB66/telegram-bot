import time
import requests
import os

from signal_logic import classify_signal
from send_alert import send_alert
from state_engine import should_alert

API_KEY = os.getenv("FINNHUB_API_KEY")

print("=" * 60)
print("IAL STARTUP DIAGNOSTICS")
print("=" * 60)
if API_KEY:
    print("FINNHUB KEY FOUND: YES")
    print("KEY LENGTH:", len(API_KEY))
    print(f"KEY PREVIEW: {API_KEY[:2]}...{API_KEY[-2:]}")
else:
    print("FINNHUB KEY FOUND: NO")
print("=" * 60)

TICKERS = [
    "AMC", "GME", "CVNA", "UPST",
    "SOFI", "HOOD", "AFRM", "DKNG",
    "MARA", "RIOT", "COIN",
    "AI", "PLTR",
    "LCID", "RIVN", "NIO", "XPEV"
]

CHECK_INTERVAL = 30

CANDLE_RESOLUTION = "1"
CANDLE_LOOKBACK_SECONDS = 259200
CANDLE_DELAY_SECONDS = 300

def get_json(url, label):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"{label} HTTP ERROR:", response.status_code, response.text[:200])
            return None
        return response.json()
    except Exception as e:
        print(f"{label} REQUEST ERROR:", e)
        return None

def get_market_data(symbol):
    try:
        if not API_KEY:
            print("ERROR: FINNHUB_API_KEY not found")
            return None
        quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"
        quote = get_json(quote_url, f"{symbol} QUOTE")
        if not quote:
            return None
        price = float(quote.get("c", 0))
        prev_close = float(quote.get("pc", 0))
        if price == 0 or prev_close == 0:
            print(f"{symbol} QUOTE BAD:", quote)
            return None
        change_pct = ((price - prev_close) / prev_close) * 100
        now = int(time.time()) - CANDLE_DELAY_SECONDS
        start = now - CANDLE_LOOKBACK_SECONDS
        candle_url = (
            f"https://finnhub.io/api/v1/stock/candle"
            f"?symbol={symbol}&resolution={CANDLE_RESOLUTION}"
            f"&from={start}&to={now}&token={API_KEY}"
        )
        candles = get_json(candle_url, f"{symbol} CANDLES")
        if not candles:
            return None
        status = candles.get("s", "missing")
        closes = candles.get("c", [])
        volumes = candles.get("v", [])
        timestamps = candles.get("t", [])
        print(f"{symbol} DATA CHECK | QUOTE OK | CANDLE STATUS: {status} | CLOSES: {len(closes)} | VOLUMES: {len(volumes)} | TIMES: {len(timestamps)}")
        if status != "ok":
            print(f"{symbol} CANDLE BAD:", candles)
            return None
        cleaned=[(c,v) for c,v in zip(closes,volumes) if c is not None and v is not None and float(c)>0 and float(v)>0]
        if len(cleaned)<5:
            print(f"{symbol} CANDLE INSUFFICIENT AFTER CLEANING:", len(cleaned))
            return None
        closes=[float(x[0]) for x in cleaned]
        volumes=[float(x[1]) for x in cleaned]
        return {"price":price,"change_pct":change_pct,"closes":closes,"volumes":volumes}
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def build_structure(market_data):
    change_pct=market_data["change_pct"];closes=market_data["closes"];volumes=market_data["volumes"]
    current_volume=volumes[-1];prior=volumes[:-1];avg=sum(prior)/max(len(prior),1);rvol=0 if avg==0 else current_volume/avg
    recent_change=0 if closes[-4]==0 else ((closes[-1]-closes[-4])/closes[-4])*100
    volume="EXTREME" if rvol>=3 else "SURGING" if rvol>=2.5 else "EXPANDING" if rvol>=2 else "ELEVATED" if rvol>=1.5 else "NORMAL"
    if change_pct>=10 and recent_change<=0: velocity="STALLING"
    elif recent_change>=1: velocity="EXTREME"
    elif recent_change>=0.5: velocity="ACCELERATING"
    elif recent_change>=0.2: velocity="HIGH"
    elif recent_change<=-0.5: velocity="REVERSING"
    elif recent_change>=0: velocity="BUILDING"
    else: velocity="MODERATE"
    return volume,velocity,rvol,recent_change

def run():
    print("IAL ENGINE LIVE â€” CANDLE PIPELINE RESTORE v1.0")
    while True:
        for symbol in TICKERS:
            try:
                md=get_market_data(symbol)
                if not md:
                    print(f"SKIPPING {symbol} â€” bad data");continue
                price=md["price"];change_pct=md["change_pct"]
                volume,velocity,rvol,recent_change=build_structure(md)
                signal=classify_signal(price,change_pct,volume,velocity)
                state=signal.get("state","UNKNOWN")
                if state=="BASELINE":
                    print(f"BASELINE: {symbol} | {round(change_pct,2)}% | RVOL {round(rvol,2)} | RECENT {round(recent_change,2)}% | {volume}/{velocity}")
                    continue
                if should_alert(symbol,state):
                    send_alert(symbol,price,change_pct,signal);print(f"SENT CLEAN: {symbol} - {state}")
                else:
                    print(f"NO DUPLICATE: {symbol} - {state}")
            except Exception as e:
                print(f"Error with {symbol}: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__=="__main__":
    run()
