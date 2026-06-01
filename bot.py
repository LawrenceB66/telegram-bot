import requests
import time
import os

import json
from send_alert import send_alert

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

CHECK_INTERVAL = 30
COOLDOWN_SECONDS = 300

STATE_FILE = "state.json"

TICKERS = ["AMC","GME","CVNA","UPST"]

def run():
    print("RUNNING CLEAN TEST")

    while True:
        for ticker in TICKERS:
            message = f"TEST #{ticker}"
            send_alert(message)
            time.sleep(2)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run()
