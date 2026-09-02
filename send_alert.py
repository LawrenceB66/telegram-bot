import os

import requests


BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def _ordinal(number):
    number = int(number)

    if 10 <= number % 100 <= 20:
        suffix = "th"

    else:
        suffix = {
            1: "st",
            2: "nd",
            3: "rd",
        }.get(
            number % 10,
            "th"
        )

    return f"{number}{suffix}"


def _alert_descriptor(signal_name):
    if not signal_name:
        return ""

    name = str(
        signal_name
    ).strip().upper()

    # ==================================================
    # BEARISH / DETERIORATION
    # ==================================================

    if "DOWNSIDE MOMENTUM" in name:
        return "Downside Momentum"

    if "DOWNSIDE EXPANSION" in name:
        return "Downside Expansion"

    if "PRICE COOLING" in name:
        return "Price Cooling"

    if "BREAKDOWN" in name:
        return "Breakdown"

    # ==================================================
    # BULLISH / PRESSURE
    # ==================================================

    if "MOMENTUM SURGE" in name:
        return "Momentum"

    if "ACTIVE EXPANSION" in name:
        return "Expansion"

    if "PRESSURE" in name:
        return "Pressure"

    if "PRICE STALL" in name:
        return "Price Stall"

    # ==================================================
    # LEGACY
    # ==================================================

    if "EXHAUSTION" in name:
        return "Exhaustion"

    return ""


def send_alert(
    symbol,
    price,
    change_pct,
    signal,
    rvol=None,
    participation_pct=None,
):
    try:
        if signal is None:
            print(
                f"SKIPPING — SIGNAL IS NONE: {symbol}"
            )
            return

        if not BOT_TOKEN or not CHAT_ID:
            print(
                "ERROR: Missing TELEGRAM_TOKEN or CHAT_ID"
            )
            return

        price_str = (
            f"{float(price):.2f}"
        )

        change_str = (
            f"{float(change_pct):+.2f}%"
        )

        emoji = signal.get(
            "emoji",
            ""
        )

        name = signal.get(
            "name",
            ""
        )

        volume = signal.get(
            "volume",
            "N/A"
        )

        notes = signal.get(
            "read",
            ""
        )

        event_type = signal.get(
            "event_type"
        )

        alert_count = int(
            signal.get(
                "alert_count",
                1
            )
        )

        # ==================================================
        # ALERT DISPLAY
        # ==================================================

        descriptor = _alert_descriptor(
            name
        )

        if descriptor:
            alert_line = (
                f"{emoji} "
                f"{descriptor} • "
                f"{_ordinal(alert_count)} Alert"
            ).strip()

        else:
            alert_line = (
                f"{emoji} "
                f"{_ordinal(alert_count)} Alert"
            ).strip()

        # ==================================================
        # VOLUME DISPLAY
        # ==================================================

        if participation_pct is not None:
            participation_str = (
                f"{float(participation_pct):+.0f}%"
            )

            volume_line = (
                f"{participation_str} "
                f"({volume})"
            )

        elif rvol is not None:
            volume_line = (
                f"{float(rvol):.2f}x RVOL "
                f"({volume})"
            )

        else:
            volume_line = volume

        # ==================================================
        # TELEGRAM MESSAGE
        # ==================================================

        message = (
            f"#{symbol}\n"
            f"\n"
            f"Price: ${price_str} • "
            f"{change_str}\n"
            f"Volume: {volume_line}\n"
            f"\n"
            f"{alert_line}\n"
        )

        if notes:
            message += (
                f"\n"
                f"Notes: {notes}"
            )

        url = (
            f"https://api.telegram.org/"
            f"bot{BOT_TOKEN}/sendMessage"
        )

        payload = {
            "chat_id": CHAT_ID,
            "text": message,
        }

        response = requests.post(
            url,
            data=payload,
            timeout=10,
        )

        if response.status_code == 200:
            print(
                f"ALERT SENT: "
                f"{symbol} - {name} | "
                f"{event_type or 'NEW_EVENT'} | "
                f"ALERT {alert_count}"
            )

        else:
            print(
                f"Telegram Error: "
                f"{response.status_code} | "
                f"{response.text}"
            )

    except Exception as e:
        print(
            f"Send alert error: {e}"
        )
