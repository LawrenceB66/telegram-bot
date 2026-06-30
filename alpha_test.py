import os

import requests

import json

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

print("=" * 60)

print("IAL ALPHA VANTAGE TEST")

print("=" * 60)

if not API_KEY:

    print("ERROR: ALPHA_VANTAGE_API_KEY not found.")

    exit()

print("KEY FOUND")

print("KEY LENGTH:", len(API_KEY))

print(f"KEY PREVIEW: {API_KEY[:2]}...{API_KEY[-2:]}")

symbol = "AMC"

url = (

    "https://www.alphavantage.co/query"

    f"?function=TIME_SERIES_INTRADAY"

    f"&symbol={symbol}"

    f"&interval=1min"

    f"&entitlement=realtime"

    f"&apikey={API_KEY}"

)

print("\nREQUEST URL:")

print(url.replace(API_KEY, "********"))

print("\nREQUESTING DATA...\n")

try:

    response = requests.get(url, timeout=20)

    print("HTTP STATUS:", response.status_code)

    data = response.json()

    print("\nRAW RESPONSE:\n")

    print(json.dumps(data, indent=4))

except Exception as e:

    print("REQUEST FAILED:")

    print(e)
