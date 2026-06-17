# =========================
# STATE ENGINE (LOCKED)
# =========================

import json
import os

STATE_FILE = "state.json"


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"State load error: {e}")
        return {}


def save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)
    except Exception as e:
        print(f"State save error: {e}")


def should_alert(symbol, new_state):
    state = load_state()

    last_state = state.get(symbol)

    # 🚫 NO DUPLICATES
    if last_state == new_state:
        return False

    # ✅ UPDATE STATE
    state[symbol] = new_state
    save_state(state)

    return True
