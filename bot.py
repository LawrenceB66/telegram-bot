import requests

import time

TOKEN = "8669632802:AAHA3k2HtlnDcW6gYcwFIRP9g5mWBQ6zMDc"

CHANNEL_ID = -1003667470993

URL = f"https://api.telegram.org/bot{TOKEN}/"

def send_message(chat_id, text):

    requests.get(URL + "sendMessage", params={

        "chat_id": chat_id,

        "text": text

    })

def get_updates():

    return requests.get(URL + "getUpdates").json()

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

                    if text.lower() == "/start":
                        send_message(chat_id, "Bot is live 🚀")
                        send_message(CHANNEL_ID, "🚀 Connected to channel")

                    elif text.lower() == "test":
                        send_message(CHANNEL_ID, "📡 test alert working")

                    else:
                        print("Ignored:", text)
                    

        time.sleep(2)

if __name__ == "__main__":

    main()