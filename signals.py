"""signals.py: the indicator maths and the entry rules, shared by backtest.py and scan.py.

Because both programs import this one file, the backtest and the daily scan
always agree. It uses only Python's standard library.
All indicators use daily closing prices. A value of None means "not enough
history yet".
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------- indicators ----------

def sma(values, n):
    """Simple average of the last n values (including today)."""
    out = [None] * len(values)
    total = 0.0
    for i, v in enumerate(values):
        total += v
        if i >= n:
            total -= values[i - n]
        if i >= n - 1:
            out[i] = total / n
    return out


def rsi(closes, n):
    """RSI with Wilder's smoothing: 0 to 100, low means the stock has fallen hard."""
    out = [None] * len(closes)
    if len(closes) <= n:
        return out
    changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gain = sum(max(c, 0) for c in changes[:n]) / n
    loss = sum(max(-c, 0) for c in changes[:n]) / n
    out[n] = 100.0 if loss == 0 else 100 - 100 / (1 + gain / loss)
    for i in range(n + 1, len(closes)):
        c = changes[i - 1]
        gain = (gain * (n - 1) + max(c, 0)) / n
        loss = (loss * (n - 1) + max(-c, 0)) / n
        out[i] = 100.0 if loss == 0 else 100 - 100 / (1 + gain / loss)
    return out


def atr(highs, lows, closes, n):
    """Average True Range with Wilder's smoothing: the stock's average daily move."""
    out = [None] * len(closes)
    if len(closes) <= n:
        return out
    true_range = [highs[0] - lows[0]]
    for i in range(1, len(closes)):
        true_range.append(max(highs[i] - lows[i],
                              abs(highs[i] - closes[i - 1]),
                              abs(lows[i] - closes[i - 1])))
    value = sum(true_range[1:n + 1]) / n
    out[n] = value
    for i in range(n + 1, len(closes)):
        value = (value * (n - 1) + true_range[i]) / n
        out[i] = value
    return out


def highest_previous_close(closes, n):
    """The highest close of the n days before today (today is not included)."""
    out = [None] * len(closes)
    for i in range(n, len(closes)):
        out[i] = max(closes[i - n:i])
    return out


def change_over(closes, n):
    """The gain over the last n trading days, as a fraction (0.10 = up 10%)."""
    out = [None] * len(closes)
    for i in range(n, len(closes)):
        out[i] = closes[i] / closes[i - n] - 1
    return out


def indicators(highs, lows, closes):
    """Every indicator the rules need, for one stock."""
    return {
        "close": closes,
        "sma200": sma(closes, 200),
        "high55": highest_previous_close(closes, 55),
        "rsi2": rsi(closes, 2),
        "rsi14": rsi(closes, 14),
        "atr14": atr(highs, lows, closes, 14),
        "gain6m": change_over(closes, 126),  # about six months of trading days
    }


# ---------- the entry rules ----------
# Each rule looks at one stock on one day (index i) and answers yes or no.

def breakout(ind, i):
    """Close above the highest close of the previous 55 days, and above the 200-day average."""
    if ind["high55"][i] is None or ind["sma200"][i] is None:
        return False
    return ind["close"][i] > ind["high55"][i] and ind["close"][i] > ind["sma200"][i]


def pullback(ind, i):
    """Close above the 200-day average, with the 2-day RSI below 10."""
    if ind["sma200"][i] is None or ind["rsi2"][i] is None:
        return False
    return ind["close"][i] > ind["sma200"][i] and ind["rsi2"][i] < 10


def bounce(ind, i):
    """The 14-day RSI below 30."""
    return ind["rsi14"][i] is not None and ind["rsi14"][i] < 30


RULES = {"breakout": breakout, "pullback": pullback, "bounce": bounce}

RULE_NAMES = {
    "breakout": "Breakout (55-day high, above 200-day average)",
    "pullback": "Pullback (2-day RSI below 10, above 200-day average)",
    "bounce": "Oversold bounce (14-day RSI below 30)",
}


def rank_score(ind, i):
    """When more stocks qualify than there are free slots, the biggest
    six-month gain goes first."""
    score = ind["gain6m"][i]
    return score if score is not None else -1e9


# ---------- the numbers in rules.md ----------

def load_rules(path=None):
    """Read the size, limits, stop, target and time limit out of rules.md."""
    settings = {"size": 0.20, "max_positions": 5, "daily_limit": 0.03,
                "stop_atr": 2.0, "target_atr": 4.0, "time_limit": 30, "entry": ""}
    path = path or os.path.join(HERE, "rules.md")
    if not os.path.exists(path):
        return settings
    number = r"(\d+(?:\.\d+)?)"
    with open(path, encoding="utf-8") as f:
        for line in f:
            name, _, text = line.partition(":")
            name, text = name.strip().lower(), text.strip()
            if name == "size" and re.search(number + r"\s*%", text):
                settings["size"] = float(re.search(number + r"\s*%", text).group(1)) / 100
            elif name == "stop" and re.search(number + r"\s*x\s*ATR", text, re.I):
                settings["stop_atr"] = float(re.search(number + r"\s*x\s*ATR", text, re.I).group(1))
            elif name == "target" and re.search(number + r"\s*x\s*ATR", text, re.I):
                settings["target_atr"] = float(re.search(number + r"\s*x\s*ATR", text, re.I).group(1))
            elif name == "time limit" and re.search(r"after\s+(\d+)", text):
                settings["time_limit"] = int(re.search(r"after\s+(\d+)", text).group(1))
            elif name == "limits":
                if re.search(r"(\d+)\s+positions", text):
                    settings["max_positions"] = int(re.search(r"(\d+)\s+positions", text).group(1))
                if re.search(r"down\s+" + number + r"\s*%", text):
                    settings["daily_limit"] = float(re.search(r"down\s+" + number + r"\s*%", text).group(1)) / 100
            elif name == "entry":
                settings["entry"] = text
    return settings


def entry_rule_name(entry_text):
    """Work out which rule the Entry line in rules.md describes, or None."""
    text = entry_text.lower()
    for name in RULES:
        if name in text:
            return name
    return None
