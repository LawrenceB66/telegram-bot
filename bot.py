import requests
import time
import os
import re

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = -1003667470993

URL = f"https://api.telegram.org/bot{TOKEN}/"

top5_watchlist = []


def send_message(chat_id, text):
    requests.get(URL + "sendMessage", params={
        "chat_id": chat_id,
        "text": text
    })


def get_updates(offset=None):
    params = {"timeout": 100}
    if offset:
        params["offset"] = offset
    return requests.get(URL + "getUpdates", params=params).json()


def clean_ticker(ticker):
    return "$" + ticker.replace("$", "").upper()


def extract_ticker(line):
    match = re.search(r"\$?[A-Z]{1,5}", line.upper())
    if match:
        return clean_ticker(match.group())
    return None


def handle_top5(text):
    global top5_watchlist

    raw = text.split(":")[-1].strip().split()
    top5_watchlist = [clean_ticker(t) for t in raw][:5]

    message = "📊 TOP 5 — TODAY\n\n"
    message += "\n".join(top5_watchlist)
    message += """

—

Focus: Momentum + Pressure Alignment
Execution: Selective

#Top5
"""
    send_message(CHANNEL_ID, message)


def ticker_allowed(ticker):
    return ticker in top5_watchlist


def send_breakout(ticker):
    send_message(CHANNEL_ID, f"""🚨 BREAKOUT ALERT

{ticker}

Momentum Expansion — Active

Volume accelerating
Pressure releasing

—

Classification: Breakout
Status: Active
Timeframe: Intraday

#Breakout""")


def send_pressure(ticker):
    send_message(CHANNEL_ID, f"""⚡ PRESSURE COOKER

{ticker}

Compression building — No release yet

Volume steady
Range tightening

—

Classification: Pressure
Status: Building
Timeframe: Intraday

#Pressure""")


def send_ticking(ticker):
    send_message(CHANNEL_ID, f"""💣 TICKING TIME BOMB

{ticker}

Trigger proximity — Immediate reaction zone

Low DTC
High sensitivity

—

Classification: Pre-Breakout
Status: Ready
Timeframe: Short-term

#Ready""")


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
    if text.lower() == "test":
        send_message(CHANNEL_ID, "⚙️ Test alert working")
        return

    if text.lower().startswith("top 5"):
        handle_top5(text)
        return

    for line in text.split("\n"):
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
