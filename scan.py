"""scan.py: checks every stock in stocks.txt against the entry rule in rules.md.

Run it with:  python scan.py --live              (fresh daily prices from Alpaca)
         or:  python scan.py --date 2026-11-09   (as of a past date, from prices.csv)

It prints one table of the stocks that qualify, best first, with the stop and
target each trade would get. It uses the same maths as backtest.py (signals.py)
and only Python's standard library. It doesn't look at the account: checking
holdings and limits is the morning job's work.
"""
import argparse
import csv
import os
import sys
from datetime import date, timedelta

import signals

HERE = os.path.dirname(os.path.abspath(__file__))


def read_stocks():
    with open(os.path.join(HERE, "stocks.txt"), encoding="utf-8") as f:
        return [line.strip().upper() for line in f if line.strip()]


def live_bars(stocks):
    """About the last 300 finished daily bars for each stock, from Alpaca."""
    from get_prices import fetch_bars
    return fetch_bars(stocks, date.today() - timedelta(days=450))


def csv_bars(stocks, as_of):
    """Daily bars from prices.csv, up to and including the as_of date."""
    path = os.path.join(HERE, "prices.csv")
    if not os.path.exists(path):
        sys.exit("prices.csv not found. Run get_prices.py first, or use --live.")
    out = {s: [] for s in stocks}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["symbol"] in out and row["date"] <= as_of:
                out[row["symbol"]].append({"date": row["date"], "high": float(row["high"]),
                                           "low": float(row["low"]), "close": float(row["close"])})
    return out


def main():
    parser = argparse.ArgumentParser(description="Scan the desk's stocks for the entry rule.")
    parser.add_argument("--live", action="store_true", help="fetch fresh daily prices from Alpaca")
    parser.add_argument("--date", help="scan as of this date (YYYY-MM-DD) using prices.csv")
    args = parser.parse_args()

    settings = signals.load_rules()
    rule = signals.entry_rule_name(settings["entry"])
    if rule is None:
        sys.exit("rules.md has no entry rule that scan.py knows (breakout, pullback or bounce).")

    stocks = read_stocks()
    if args.live and not args.date:
        bars = live_bars(stocks)
    else:
        bars = csv_bars(stocks, args.date or "9999-12-31")

    found, last_days = [], set()
    for symbol in stocks:
        b = bars.get(symbol) or []
        if not b:
            print(f"Warning: no prices for {symbol}")
            continue
        last_days.add(b[-1]["date"])
        ind = signals.indicators([x["high"] for x in b], [x["low"] for x in b], [x["close"] for x in b])
        i = len(b) - 1
        if signals.RULES[rule](ind, i) and ind["atr14"][i] is not None:
            found.append((signals.rank_score(ind, i), symbol, ind, i))
    found.sort(reverse=True)

    as_of = max(last_days) if last_days else "no data"
    print(f"Entry rule: {signals.RULE_NAMES[rule]}")
    print(f"Prices as of the close on {as_of}. Checked {len(stocks)} stocks, {len(found)} qualify.")
    if len(last_days) > 1:
        print(f"Warning: the stocks don't all end on the same day: {sorted(last_days)}")
    if not found:
        print("Nothing qualifies today.")
        return

    # Stop and target here are estimates from the last close. The real ones are
    # set from the price actually paid.
    print()
    print("| Rank | Stock | Close | 55-day high | 200-day avg | 6-month gain | ATR(14) | Stop (est.) | Target (est.) |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for rank, (_, symbol, ind, i) in enumerate(found, start=1):
        close, atr = ind["close"][i], ind["atr14"][i]
        gain = ind["gain6m"][i]
        print(f"| {rank} | {symbol} | {close:.2f} | {ind['high55'][i]:.2f} | {ind['sma200'][i]:.2f} | "
              f"{'n/a' if gain is None else format(gain, '+.1%')} | {atr:.2f} | "
              f"{close - settings['stop_atr'] * atr:.2f} | {close + settings['target_atr'] * atr:.2f} |")


if __name__ == "__main__":
    main()
