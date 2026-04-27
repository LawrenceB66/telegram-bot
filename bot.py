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

def get_updates():
    return requests.get(URL + "getUpdates").json()

def handle_message(text, chat_id):
    if text == "/start":
        send_message(chat_id, "Bot is live 🚀")
        send_message(CHANNEL_ID, "🚀 Connected to channel")

    elif text == "test":
        send_message(CHANNEL_ID, "📡 test alert working")

    elif any(keyword in text for keyword in BREAKOUT_KEYWORDS):
        send_message(CHANNEL_ID, f"""
🚨 BREAKOUT ALERT

{text}

⚠️ Real-time abnormal movement detected
""")

    else:
        print("Ignored:", text)

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
                    text = msg.get("text", "")
                    chat_id = msg["chat"]["id"]

                    print(f"Received: {text}")
                    handle_message(text.lower(), chat_id)

        time.sleep(2)

if __name__ == "__main__":
    main()
