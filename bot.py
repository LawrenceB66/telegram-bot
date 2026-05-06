import requests
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = -1003667470993

URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

response = requests.post(URL, data={
    "chat_id": CHANNEL_ID,
    "text": "🚨 DIRECT TEST — IF YOU SEE THIS, BOT IS WORKING 🚨"
})

print(response.text)
