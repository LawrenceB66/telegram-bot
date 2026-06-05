def format_message(symbol, price, change, state, volume, velocity):
    emoji = EMOJI_MAP.get(state, "")

    return f"""{symbol}

Price: {price:.2f} • {change:.2f}%

{emoji}

Structure:
Volume: {volume}
Velocity: {velocity}"""
