"""backtest.py: tests the entry rules day by day on the prices in prices.csv.

Run it with:  uv run --with matplotlib backtest.py
Options:      --rule breakout|pullback|bounce|all   --start YYYY-MM-DD
              --end YYYY-MM-DD   --cash 10000   --title "text for the chart"

How it trades (the same for every rule):
- A signal uses a day's closing prices, and the trade buys at the next day's open.
- Size, limits, stop, target and time limit come from rules.md.
- Every buy and every sell costs 0.05%.
- If the stop and the target are both hit on the same day, the stop was hit first.
This is a simulation on past prices, not a track record.
"""
import argparse
import csv
import math
import os
from datetime import date

import signals

HERE = os.path.dirname(os.path.abspath(__file__))
FEE = 0.0005  # 0.05% on every buy and every sell


def load_prices():
    """Read prices.csv into {symbol: {"date": [...], "open": [...], ...}}."""
    data = {}
    with open(os.path.join(HERE, "prices.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            s = data.setdefault(row["symbol"], {"date": [], "open": [], "high": [], "low": [], "close": []})
            s["date"].append(row["date"])
            for column in ("open", "high", "low", "close"):
                s[column].append(float(row[column]))
    for s in data.values():
        s["index"] = {d: i for i, d in enumerate(s["date"])}  # date -> row number
        s["ind"] = signals.indicators(s["high"], s["low"], s["close"])
    return data


def simulate(rule, data, stocks, days, first, last, cash, settings):
    """Run one rule from days[first] to days[last]. Returns (equity per day, trades)."""
    rule_fn = signals.RULES[rule]
    positions = {}   # symbol -> the open trade
    trades = []      # every finished trade
    equity = []      # account value at each close

    def candidates(day, account_value):
        """The stocks that qualify at this day's close, best first, for the free slots."""
        found = []
        for symbol in stocks:
            i = data[symbol]["index"].get(day)
            if symbol in positions or i is None:
                continue
            ind = data[symbol]["ind"]
            if rule_fn(ind, i) and ind["atr14"][i] is not None:
                found.append((signals.rank_score(ind, i), symbol, i))
        found.sort(reverse=True)
        free = settings["max_positions"] - len(positions)
        orders = []
        for _, symbol, i in found[:max(free, 0)]:
            close = data[symbol]["close"][i]
            shares = math.floor(settings["size"] * account_value / close)
            orders.append({"symbol": symbol, "shares": shares, "atr": data[symbol]["ind"]["atr14"][i],
                           "signal_date": day})
        return orders

    def sell(symbol, price, day, reason):
        nonlocal cash
        p = positions.pop(symbol)
        cash += p["shares"] * price * (1 - FEE)
        cost = p["shares"] * p["entry"] * (1 + FEE)
        profit = p["shares"] * price * (1 - FEE) - cost
        trades.append({"rule": rule, "symbol": symbol, "shares": p["shares"],
                       "entry_date": p["entry_date"], "entry_price": round(p["entry"], 4),
                       "stop": round(p["stop"], 4), "target": round(p["target"], 4),
                       "exit_date": day, "exit_price": round(price, 4), "reason": reason,
                       "profit": round(profit, 2), "return_pct": round(100 * profit / cost, 2)})

    # Signals from the close before the first day become the first morning's orders.
    pending = candidates(days[first - 1], cash) if first > 0 else []
    blocked = False          # True the morning after the account fell by the daily limit
    previous_value = cash

    for k in range(first, last + 1):
        day = days[k]
        bars = {}
        for symbol in set(positions) | {o["symbol"] for o in pending}:
            i = data[symbol]["index"].get(day)
            if i is not None:
                s = data[symbol]
                bars[symbol] = (s["open"][i], s["high"][i], s["low"][i], s["close"][i])

        # 1. At the open: sell trades that have reached the time limit.
        for symbol in list(positions):
            if symbol in bars and k - positions[symbol]["k"] >= settings["time_limit"]:
                sell(symbol, bars[symbol][0], day, "time limit")

        # 2. At the open: buy yesterday's signals (unless the daily limit blocks new trades).
        bought_today = set()
        if not blocked:
            for order in pending:
                symbol = order["symbol"]
                if symbol not in bars or symbol in positions or len(positions) >= settings["max_positions"]:
                    continue
                price = bars[symbol][0]
                cost = order["shares"] * price * (1 + FEE)
                if order["shares"] < 1 or cost > cash:
                    continue  # not enough cash: skip the trade
                cash -= cost
                positions[symbol] = {"shares": order["shares"], "entry": price, "entry_date": day, "k": k,
                                     "stop": price - settings["stop_atr"] * order["atr"],
                                     "target": price + settings["target_atr"] * order["atr"]}
                bought_today.add(symbol)

        # 3. During the day: check every trade against its stop and its target.
        for symbol in list(positions):
            if symbol not in bars:
                continue
            open_, high, low, _ = bars[symbol]
            p = positions[symbol]
            if symbol not in bought_today and open_ <= p["stop"]:
                sell(symbol, open_, day, "stop (gap at open)")
            elif symbol not in bought_today and open_ >= p["target"]:
                sell(symbol, open_, day, "target (gap at open)")
            elif low <= p["stop"]:           # the stop is checked first, so it wins a tie
                sell(symbol, p["stop"], day, "stop")
            elif high >= p["target"]:
                sell(symbol, p["target"], day, "target")

        # 4. At the close: value the account and check the daily limit.
        value = cash
        for symbol, p in positions.items():
            i = data[symbol]["index"].get(day)
            price = data[symbol]["close"][i] if i is not None else p["entry"]
            value += p["shares"] * price
        equity.append(value)
        blocked = value / previous_value - 1 <= -settings["daily_limit"]
        previous_value = value

        # 5. At the close: find tomorrow morning's orders.
        pending = candidates(day, value)

    # Trades still open on the last day are listed, valued at the last close.
    for symbol, p in positions.items():
        price = data[symbol]["close"][data[symbol]["index"][days[last]]]
        cost = p["shares"] * p["entry"] * (1 + FEE)
        trades.append({"rule": rule, "symbol": symbol, "shares": p["shares"],
                       "entry_date": p["entry_date"], "entry_price": round(p["entry"], 4),
                       "stop": round(p["stop"], 4), "target": round(p["target"], 4),
                       "exit_date": "", "exit_price": round(price, 4), "reason": "still open",
                       "profit": round(p["shares"] * price - cost, 2),
                       "return_pct": round(100 * (p["shares"] * price - cost) / cost, 2)})
    return equity, trades


def hold(data, symbols, days, first, last, cash):
    """Buy the symbols in equal parts at the first day's open and hold them."""
    shares = {s: (cash / len(symbols)) / (data[s]["open"][data[s]["index"][days[first]]] * (1 + FEE))
              for s in symbols}
    return [sum(n * data[s]["close"][data[s]["index"][days[k]]] for s, n in shares.items())
            for k in range(first, last + 1)]


def stats(equity, dates, cash, trades=None):
    """The numbers for one line of the results table."""
    returns = [equity[i] / equity[i - 1] - 1 for i in range(1, len(equity))]
    mean = sum(returns) / len(returns)
    spread = math.sqrt(sum((r - mean) ** 2 for r in returns) / (len(returns) - 1))
    peak, worst = cash, 0.0
    for value in equity:
        peak = max(peak, value)
        worst = min(worst, value / peak - 1)
    years, start_value = {}, cash
    for year in sorted({d[:4] for d in dates}):
        end_value = [v for d, v in zip(dates, equity) if d[:4] == year][-1]
        years[year] = end_value / start_value - 1
        start_value = end_value
    out = {"end": equity[-1], "return": equity[-1] / cash - 1, "drawdown": worst,
           "sharpe": mean / spread * math.sqrt(252) if spread else 0.0, "years": years}
    if trades is not None:
        closed = [t for t in trades if t["reason"] != "still open"]
        wins = [t["return_pct"] for t in closed if t["profit"] > 0]
        losses = [t["return_pct"] for t in closed if t["profit"] <= 0]
        out.update({"trades": len(closed), "win_rate": len(wins) / len(closed) if closed else 0.0,
                    "avg_win": sum(wins) / len(wins) if wins else 0.0,
                    "avg_loss": sum(losses) / len(losses) if losses else 0.0})
    return out


def main():
    parser = argparse.ArgumentParser(description="Backtest the desk's entry rules on prices.csv.")
    parser.add_argument("--rule", default="all", choices=list(signals.RULES) + ["all"])
    parser.add_argument("--start", help="first day, YYYY-MM-DD (default: five years before the end)")
    parser.add_argument("--end", help="last day, YYYY-MM-DD (default: the last day in prices.csv)")
    parser.add_argument("--cash", type=float, default=10000)
    parser.add_argument("--title", default="Backtest on past prices. A simulation, not a track record.")
    args = parser.parse_args()

    settings = signals.load_rules()
    data = load_prices()
    with open(os.path.join(HERE, "stocks.txt"), encoding="utf-8") as f:
        stocks = [line.strip().upper() for line in f if line.strip()]
    days = data["SPY"]["date"]  # the market's trading days

    end = args.end or days[-1]
    if args.start:
        start = args.start
    else:
        e = date.fromisoformat(end)
        start = date(e.year - 5, e.month, min(e.day, 28)).isoformat()
    first = next(i for i, d in enumerate(days) if d >= start)
    last = max(i for i, d in enumerate(days) if d <= end)
    dates = days[first:last + 1]

    rules = list(signals.RULES) if args.rule == "all" else [args.rule]
    lines, all_trades = [], []
    for rule in rules:
        equity, trades = simulate(rule, data, stocks, days, first, last, args.cash, settings)
        lines.append((signals.RULE_NAMES[rule], equity, stats(equity, dates, args.cash, trades)))
        all_trades += trades
    spy = hold(data, ["SPY"], days, first, last, args.cash)
    lines.append(("Hold the S&P 500 (SPY)", spy, stats(spy, dates, args.cash)))
    basket = hold(data, stocks, days, first, last, args.cash)
    lines.append((f"Hold all {len(stocks)} stocks", basket, stats(basket, dates, args.cash)))

    # The results table.
    years = sorted(lines[0][2]["years"])
    print(f"Test period: {dates[0]} to {dates[-1]} ({len(dates)} trading days), starting with ${args.cash:,.0f}")
    print(f"Rules used: {settings['size']:.0%} per trade, {settings['max_positions']} positions max, "
          f"stop {settings['stop_atr']:g} x ATR, target {settings['target_atr']:g} x ATR, "
          f"{settings['time_limit']}-day time limit, {settings['daily_limit']:.0%} daily limit")
    print()
    header = ["Strategy", "End value", "Return", "Max drawdown", "Sharpe", "Trades", "Win rate",
              "Avg win", "Avg loss"] + years
    print("| " + " | ".join(header) + " |")
    print("|" + " --- |" * len(header))
    for name, _, s in lines:
        row = [name, f"${s['end']:,.0f}", f"{s['return']:+.1%}", f"{s['drawdown']:.1%}", f"{s['sharpe']:.2f}"]
        if "trades" in s:
            row += [str(s["trades"]), f"{s['win_rate']:.0%}", f"{s['avg_win']:+.1f}%", f"{s['avg_loss']:+.1f}%"]
        else:
            row += ["1" if "S&P" in name else str(len(stocks)), "-", "-", "-"]
        row += [f"{s['years'][y]:+.1%}" for y in years]
        print("| " + " | ".join(row) + " |")

    # Every trade, in trades.csv.
    columns = ["rule", "symbol", "shares", "entry_date", "entry_price", "stop", "target",
               "exit_date", "exit_price", "reason", "profit", "return_pct"]
    with open(os.path.join(HERE, "trades.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(all_trades)
    print(f"\nSaved {len(all_trades)} trades to trades.csv")

    # The chart, with every line on it.
    try:
        import matplotlib
    except ImportError:
        print("matplotlib isn't installed, so the chart was skipped. The table above is complete.")
        return
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    x = [date.fromisoformat(d) for d in dates]
    fig, ax = plt.subplots(figsize=(11, 6))
    for name, equity, _ in lines:
        is_hold = name.startswith("Hold")
        ax.plot(x, equity, label=f"{name}: ${equity[-1]:,.0f}",
                linestyle="--" if is_hold else "-", linewidth=1.4 if is_hold else 1.9)
    ax.axhline(args.cash, color="grey", linewidth=0.6)
    ax.set_title(args.title)
    ax.set_ylabel("Account value ($)")
    ax.yaxis.set_major_formatter(lambda v, _: f"${v:,.0f}")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "equity_curves.png"), dpi=130)
    print("Saved equity_curves.png")


if __name__ == "__main__":
    main()
