import os
import requests


BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


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

        price_str = f"{float(price):.2f}"
        change_str = f"{float(change_pct):.2f}"

        emoji = signal.get("emoji", "")
        name = signal.get("name", "")
        volume = signal.get("volume", "N/A")
        notes = signal.get("read", "")

        event_type = signal.get(
            "event_type"
        )

        alert_count = int(
            signal.get(
                "alert_count",
                1
            )
        )

        alert_label = signal.get(
            "alert_label"
        )

        # ==================================================
        # EVENT DISPLAY
        # ==================================================

        signal_line = (
            f"{emoji} {name}"
        )

        if event_type in [
            "CONTINUATION",
            "CONTINUATION_STATE_CHANGE",
        ]:
            if alert_count > 1 and alert_label:
                signal_line += (
                    f" — Continuation "
                    f"({alert_label})"
                )
            else:
                signal_line += (
                    " — Continuation"
                )

        elif (
            event_type == "REPEAT_ALERT"
            and alert_label
        ):
            signal_line += (
                f" — {alert_label}"
            )

        elif (
            event_type == "STATE_CHANGE"
            and alert_label
        ):
            signal_line += (
                f" — {alert_label}"
            )

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
            f"Price: ${price_str} • "
            f"{change_str}%\n"
            f"\n"
            f"{signal_line}\n"
            f"Volume: {volume_line}\n"
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
