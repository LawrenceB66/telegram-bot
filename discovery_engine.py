# =========================
# DISCOVERY ENGINE (V1 - SAFE)
# =========================

import time

# 🔒 CONFIG (DO NOT OVER-TUNE YET)
MIN_DISCOVERY_MOVE = 3.0   # % move threshold
MAX_ACTIVE_TICKERS = 50   # safety cap


def discover_tickers(market_data):
    """
    market_data format expected:
    {
        "AMC": {"price": 2.01, "change_pct": 9.84, "volume": 1200000},
        "UPST": {"price": 32.07, "change_pct": 5.88, "volume": 800000},
        ...
    }
    """

    discovered = []

    for symbol, data in market_data.items():
        try:
            change_pct = float(data.get("change_pct", 0))

            # 🎯 BASIC DISCOVERY CONDITION
            if abs(change_pct) >= MIN_DISCOVERY_MOVE:
                discovered.append(symbol)

        except Exception as e:
            print(f"Discovery error with {symbol}: {e}")

    # 🔒 SAFETY LIMIT (prevents overload)
    return discovered[:MAX_ACTIVE_TICKERS]


def build_active_list(base_watchlist, market_data):
    """
    Combines:
    - Core tickers (your current list)
    - Newly discovered movers
    """

    discovered = discover_tickers(market_data)

    # ✅ Merge + Deduplicate
    active = list(set(base_watchlist + discovered))

    return active
