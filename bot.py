import requests
import time
import os

def safe_request(url, params=None, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=(5, 30))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if "Read timed out" in str(e):
               print("[WAITING] No updates...")
            else:
                print(f"[ERROR] Attempt {attempt+1} failed: {e}")
            time.sleep(5)
    return None


# --- CONFIG ---
TOKEN = os.getenv("TOKEN")
print("TOKEN LOADED:", TOKEN)

CHANNEL_ID = -1003667470993
URL = f"https://api.telegram.org/bot{TOKEN}/"

offset = None

# --- TEST: SEND TO CHANNEL ON START ---
safe_request(URL + "sendMessage", {
    "chat_id": CHANNEL_ID,
    "text": "🚨 IAL TEST ALERT — BOT IS LIVE 🚨"
})

# --- MAIN LOOP ---
while True:
    params = {
        "timeout": 30,
        "offset": offset
    }

    data = safe_request(URL + "getUpdates", params)

    if data and data.get("result"):
        for update in data["result"]:
            offset = update["update_id"] + 1

            print("New update received")

            # OPTIONAL: echo message (for testing)
            if "message" in update and "text" in update["message"]:
                chat_id = update["message"]["chat"]["id"]
                text = update["message"]["text"]

                safe_request(URL + "sendMessage", {
                    "chat_id": chat_id,
                    "text": f"Echo: {text}"
                })

    time.sleep(1)
