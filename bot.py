import requests
import time
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = -1003667470993

URL = f"https://api.telegram.org/bot{TOKEN}/"

BREAKOUT_KEYWORDS = [
    "halt",
    "running",
    "squeeze",
    "spiking",
    "volume",
    "breaking out",
    "exploding",
    "rip",
    "ripping"
]

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

def format_alert(text):
    lines = text.strip().split("\n")

    formatted_lines = []
    top5 = None

    for line in lines:
        line = line.strip()

        # Handle Top 5
        if "top 5" in line.lower():
            tickers = line.split(":")[-1].strip().split()
            tickers = [f"${t.replace('$','').upper()}" for t in tickers]
            top5 = " ".join(tickers)
            continue

        parts = line.split()
        if len(parts) >= 2:
            ticker = parts[0].replace("$", "").upper()
            action = " ".join(parts[1:]).capitalize()
            formatted_lines.append(f"${ticker} — {action}")

    message = ""

    if any(keyword in text.lower() for keyword in BREAKOUT_KEYWORDS):
        message += "🚨 BREAKOUT ALERT\n\n"
    else:
        message += "⚡ PRESSURE FLOW\n\n"

    message += "\n".join(formatted_lines)

    if top5:
        message += f"\n\n🧠 Top 5:\n{top5}"

    return message

def handle_message(text, chat_id):
    if text == "/start":
        send_message(chat_id, "Bot is live 🚀")
        send_message(CHANNEL_ID, "🚀 Connected to channel")

    elif text == "test":
        send_message(CHANNEL_ID, "⚙️ Test alert working")

    elif "$" in text:
        formatted = format_alert(text)
        send_message(CHANNEL_ID, formatted)

    else:
        print("Ignored:", text)

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
                    handle_message(text.lower(), chat_id)

        time.sleep(2)

if __name__ == "__main__":
    main()
