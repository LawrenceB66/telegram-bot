import requests
import time
import os
import re

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = -1003667470993

URL = f"https://api.telegram.org/bot{TOKEN}/"

BREAKOUT_KEYWORDS = [
    "halt", "running", "squeeze", "spiking", "volume",
    "breaking out", "exploding", "rip", "ripping"
]

PRESSURE_KEYWORDS = [
    "watch", "building", "setup", "loading", "pressure"
]

TICKING_KEYWORDS = [
    "ready", "near", "tight", "coiling", "primed"
]


def send_message(chat_id, text):
    requests.get(URL + "sendMessage", params={
        "chat_id": chat_id,
        "text": text
    })


def get_updates():
    return requests.get(URL + "getUpdates").json()


def extract_ticker(text):
    matches = re.findall(r"\b[A-Z]{2,5}\b", text.upper())

    ignore_words = {
        "THE", "AND", "FOR", "WITH", "THIS", "THAT",
        "READY", "WATCH", "SETUP", "RUNNING", "VOLUME",
        "BREAKING", "OUT", "RIPPING", "SQUEEZE", "HALT",
        "NEAR", "TIGHT", "COILING", "PRIMED", "LOADING"
    }

    for match in matches:
        if match not in ignore_words:
            return f"${match}"

    return "$UNKNOWN"


def handle_message(raw_text, chat_id):
    text = raw_text.lower()
    ticker = extract_ticker(raw_text)

    if text == "/start":
        send_message(chat_id, "Bot is live 🚀")
        send_message(CHANNEL_ID, "🚀 Connected to channel")

    elif text == "test":
        send_message(CHANNEL_ID, "🛰️ Test alert working")

    elif "top 5" in text:
        send_message(CHANNEL_ID, f"""📊 PRE-BELL TOP 5

{raw_text}

💣 Ticking Time Bombs
⚡ Pressure Cookers
🚨 Breakout Alerts

#Top5 #ItAintLuck""")

    elif any(keyword in text for keyword in BREAKOUT_KEYWORDS):
        send_message(CHANNEL_ID, f"""🚨 BREAKOUT ALERT

{ticker}
MOMENTUM EXPANSION
ACTIVE

Volume accelerating
Pressure releasing

#Breakout""")

    elif any(keyword in text for keyword in TICKING_KEYWORDS):
        send_message(CHANNEL_ID, f"""💣 TICKING TIME BOMB

{ticker}
IMMINENT

Tight structure
Low DTC
Ready to move

#TTB""")

    elif any(keyword in text for keyword in PRESSURE_KEYWORDS):
        send_message(CHANNEL_ID, f"""⚡ PRESSURE COOKER

{ticker}
BUILDING

High DTC
Tension increasing
Positioning developing

#Pressure""")

    else:
        print("Ignored:", raw_text)


def main():
    last_update = None

    while True:
        data = get_updates()

        for result in data["result"]:
            update_id = result["update_id"]

            if last_update is None or update_id > last_update:
                last_update = update_id

                if "message" in result:
                    msg = result["message"]
                    raw_text = msg.get("text", "")
                    chat_id = msg["chat"]["id"]

                    print(f"Received: {raw_text}")
                    handle_message(raw_text, chat_id)

        time.sleep(2)


if name == "__main__":
    main()
