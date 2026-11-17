"""get_prices.py: downloads daily prices from Alpaca and saves them as prices.csv.

Run it with:  python get_prices.py
It covers five years, plus about 300 extra trading days before that, so the
200-day average already exists on the first day of the backtest.
It uses only Python's standard library, so nothing has to be installed.
The Alpaca keys come from the environment or from .env and are never printed.
"""
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
BARS_URL = "https://data.alpaca.markets/v2/stocks/bars"


def load_keys():
    """Return (key, secret) from the environment, or from .env if they're not there."""
    key = os.environ.get("ALPACA_API_KEY")
    secret = os.environ.get("ALPACA_SECRET_KEY")
    env_path = os.path.join(HERE, ".env")
    if not (key and secret) and os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" not in line or line.startswith("#"):
                    continue
                name, value = line.split("=", 1)
                value = value.strip().strip('"').strip("'")
                if name.strip() == "ALPACA_API_KEY" and not key:
                    key = value
                if name.strip() == "ALPACA_SECRET_KEY" and not secret:
                    secret = value
    if not key or not secret:
        sys.exit("Alpaca keys not found. Put them in .env (see setup.md, Part 1).")
    return key, secret


def ny_now():
    """The current time in New York, worked out without any time zone database."""
    utc = datetime.now(timezone.utc).replace(tzinfo=None)

    def nth_sunday(year, month, n):
        d = date(year, month, 1)
        d += timedelta(days=(6 - d.weekday()) % 7)  # first Sunday
        return d + timedelta(weeks=n - 1)

    # Summer time runs from the second Sunday of March to the first Sunday of November.
    start = datetime.combine(nth_sunday(utc.year, 3, 2), datetime.min.time()) + timedelta(hours=7)
    end = datetime.combine(nth_sunday(utc.year, 11, 1), datetime.min.time()) + timedelta(hours=6)
    offset = 4 if start <= utc < end else 5
    return utc - timedelta(hours=offset)


def read_stocks():
    """The tickers in stocks.txt, one per line."""
    with open(os.path.join(HERE, "stocks.txt"), encoding="utf-8") as f:
        return [line.strip().upper() for line in f if line.strip()]


def fetch_bars(symbols, start_day, feed="sip"):
    """Download finished daily bars for the symbols, from start_day until now.

    Returns {symbol: [{"date", "open", "high", "low", "close", "volume"}, ...]}.
    """
    key, secret = load_keys()
    headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}
    # The free plan can't see the latest 15 minutes, so stop 16 minutes ago.
    end = datetime.now(timezone.utc) - timedelta(minutes=16)
    params = {
        "symbols": ",".join(symbols),
        "timeframe": "1Day",
        "start": start_day.isoformat(),
        "end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "adjustment": "all",  # adjusted for splits and dividends
        "feed": feed,
        "limit": "10000",
    }
    out = {s: [] for s in symbols}
    page_token = None
    while True:
        if page_token:
            params["page_token"] = page_token
        request = urllib.request.Request(BARS_URL + "?" + urllib.parse.urlencode(params), headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 429:  # too many requests: wait and try again
                time.sleep(5)
                continue
            if error.code in (403, 422) and feed == "sip":
                print("Alpaca refused the full-market feed, so using the IEX feed. Prices may differ slightly.")
                return fetch_bars(symbols, start_day, feed="iex")
            sys.exit(f"Alpaca returned error {error.code}: {error.read().decode('utf-8', 'replace')[:300]}")
        for symbol, bars in (payload.get("bars") or {}).items():
            for b in bars:
                out[symbol].append({"date": b["t"][:10], "open": b["o"], "high": b["h"],
                                    "low": b["l"], "close": b["c"], "volume": b["v"]})
        page_token = payload.get("next_page_token")
        if not page_token:
            break

    # Before the close, today's bar isn't finished yet, so drop it.
    now = ny_now()
    if (now.hour, now.minute) < (16, 20):
        today = now.date().isoformat()
        for symbol in out:
            out[symbol] = [b for b in out[symbol] if b["date"] != today]
    for symbol in out:
        out[symbol].sort(key=lambda b: b["date"])
    return out


def main():
    symbols = read_stocks() + ["SPY"]
    today = date.today()
    # Five years, plus about 300 trading days (roughly 450 calendar days) of run-up.
    start_day = date(today.year - 5, today.month, min(today.day, 28)) - timedelta(days=450)
    print(f"Downloading daily prices for {len(symbols)} tickers from {start_day} ...")
    data = fetch_bars(symbols, start_day)

    path = os.path.join(HERE, "prices.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "symbol", "open", "high", "low", "close", "volume"])
        for symbol in symbols:
            for b in data[symbol]:
                writer.writerow([b["date"], symbol, b["open"], b["high"], b["low"], b["close"], b["volume"]])

    # Report: how many days each ticker has, and any that are missing days SPY has.
    spy_days = {b["date"] for b in data["SPY"]}
    problems = 0
    for symbol in symbols:
        days = {b["date"] for b in data[symbol]}
        missing = len(spy_days - days)
        first = data[symbol][0]["date"] if data[symbol] else "none"
        last = data[symbol][-1]["date"] if data[symbol] else "none"
        flag = f"   <-- GAP: missing {missing} days" if missing else ""
        problems += 1 if missing else 0
        print(f"{symbol:6} {len(days):5} days  {first} to {last}{flag}")
    print(f"Saved {path}")
    print("No gaps found." if not problems else f"{problems} ticker(s) have gaps, flagged above.")


if __name__ == "__main__":
    main()
