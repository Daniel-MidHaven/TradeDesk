# rules.md
Account:     Alpaca paper
Stocks:      only the ones in stocks.txt
Size:        20% of the account per trade, whole shares
Stop:        2 x ATR(14) below the entry price
Target:      4 x ATR(14) above the entry price
Time limit:  sell at the open after 30 trading days
Limits:      5 positions max. No new trades if the account is down 3% today.
Entry:       breakout. Buy at the next open when a stock closes above its highest close of the previous 55 trading days and that close is above its 200-day simple average. If more stocks qualify than there are free slots, take the biggest gain over the last six months (126 trading days) first.
Mode:        alert. Approvals of a morning run only count before the open.
