import requests
import time
import os
import re

def safe_request(url, params=None, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Attempt {attempt+1} failed: {e}")
            time.sleep(2)

    return None

TOKEN = os.getenv("TOKEN")
print("TOKEN LOADED:" TOKEN)
CHANNEL_ID = -1003667470993

URL = f"https://api.telegram.org/bot{TOKEN}/"

top5_watchlist = []
ticker_states = {}


def send_message(chat_id, text):
    params = {
        "chat_id": chat_id,
        "text": text
    }

    data = safe_request(URL + "sendMessage", params=params)

    if data is None:
        print("Failed to send message")

def get_updates(offset=None):
    params = {"timeout": 100}
    if offset:
        params["offset"] = offset

    data = safe_request(URL + "getUpdates", params=params)

    if data is None:
        print("Failed to fetch updates")
        return {"result": []}

    return data


def clean_ticker(ticker):
    return "$" + ticker.replace("$", "").upper().strip()


def extract_ticker(line):
    match = re.search(r"\$?[A-Z]{1,5}", line.upper())
    if match:
        return clean_ticker(match.group())
    return None


def handle_top5(text):
    global top5_watchlist, ticker_states

    raw = text.split(":")[-1].strip().split()
    top5_watchlist = [clean_ticker(t) for t in raw][:5]
    ticker_states = {}

    message = "📊 TOP 5 — TODAY\n\n"
    message += "\n".join(top5_watchlist)
    message += "\n\n—\n\n"
    message += "Focus:\nShort Interest + Borrow Pressure + DTC\n\n"
    message += "Bias:\nLong Gamma / Squeeze Potential\n\n"
    message += "Execution:\nSelective\n\n"
    message += "Framework:\nPre-Squeeze → Expansion → Release\n\n"
    message += "#Top5"

    send_message(CHANNEL_ID, message)


def handle_futures(text):
    body = text.split(":", 1)[-1].strip()

    message = f"""🌙 AH / FUTURES WATCH

{body}

—

Market Environment:
Risk-on / neutral / risk-off context

Implication:
Broad market tone may influence squeeze follow-through

#Futures"""

    send_message(CHANNEL_ID, message)


def ticker_allowed(ticker):
    return ticker in top5_watchlist


def set_state(ticker, state):
    ticker_states[ticker] = state


def get_state(ticker):
    return ticker_states.get(ticker, "Unclassified")


def send_ticking(ticker):
    set_state(ticker, "Ticking Time Bomb")

    send_message(CHANNEL_ID, f"""💣 TICKING TIME BOMB

{ticker}

Low-DTC setup — immediate reaction potential

Short interest elevated
Borrow pressure active

—

Classification: Pre-Squeeze
Status: Ready
Timeframe: Short-term

#Ready""")


def send_pressure(ticker):
    set_state(ticker, "Pressure Cooker")

    send_message(CHANNEL_ID, f"""⚡ PRESSURE COOKER

{ticker}

High-DTC compression — pressure building

Short interest elevated
Borrow pressure tightening

—

Classification: Pre-Squeeze
Status: Building
Timeframe: Intraday

#Pressure""")


def send_breakout(ticker):
    origin = get_state(ticker)

    send_message(CHANNEL_ID, f"""🚨 BREAKOUT ALERT

{ticker}

Momentum Expansion — Active

Volume accelerating
Pressure releasing

—

Origin: {origin}
Status: Triggered
Timeframe: Intraday

#Breakout""")


def handle_signal(line):
    ticker = extract_ticker(line)
    if not ticker:
        return

    if not ticker_allowed(ticker):
        print(f"Ignored {ticker}: not in Top 5")
        return

    text = line.lower()

    if "running" in text or "ripping" in text or "breakout" in text:
        send_breakout(ticker)

    elif "building" in text or "pressure" in text or "watch" in text:
        send_pressure(ticker)

    elif "ready" in text or "primed" in text or "coiling" in text:
        send_ticking(ticker)


def handle_message(text, chat_id):
    clean_text = text.strip()

    if clean_text.lower() == "test":
        send_message(CHANNEL_ID, "⚙️ Test alert working")
        return

    if clean_text.lower().startswith("top 5"):
        handle_top5(clean_text)
        return

    if clean_text.lower().startswith("futures"):
        handle_futures(clean_text)
        return

    for line in clean_text.split("\n"):
        handle_signal(line.strip())


def main():
    last_update = None

    while True:
        data = get_updates(last_update + 1 if last_update else None)

        for result in data.get("result", []):
            update_id = result["update_id"]

            if last_update is None or update_id > last_update:
                last_update = update_id

                if "message" in result:
                    msg = result["message"]
                    text = msg.get("text", "")
                    chat_id = msg["chat"]["id"]

                    print(f"Received: {text}")
                    handle_message(text, chat_id)

        time.sleep(2)


if __name__ == "__main__":
    main()
