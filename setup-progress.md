Setup instructions: setup.md

# Setup progress

## Part 1: Connect Alpaca and place a first trade (in progress)

- Question 1: user has an Alpaca paper account and API key.
- Question 2 (optional $10,000 second paper account): answered 2026-11-16. User said: "The Alpaca account I connected with the 10,000 paper account" — the keys they are connecting belong to the $10,000 paper account. Don't ask again; in step 7, confirm the account check shows about $10,000.
- Step 1 done: desk folder is C:\Users\Coolk\Documents\Claude_TradeDesk, setup.md is in it.
- Step 2 done: uv/uvx 0.12.3, bash available, Python 3.13.2.
- Step 3 done: .gitignore created.
- Step 4: .env created with placeholders, .claude/settings.json created. Waiting for the user to fill in .env with their paper keys themselves (never read or print .env).
- Step 5 done: .mcp.json created (standard bash version).
- Step 6 done (2026-11-16): progress file updated; user asked to fill in .env, start a new session on this folder, approve the `alpaca` server if prompted, and type "Read setup.md and carry on with the trading desk setup."

- Step 7 done (2026-11-16): `alpaca` server connected with the user's keys (the `.venv-alpaca` workaround works). Read-only check: paper account (number starts with PA), status ACTIVE, cash $10,000, portfolio value $10,000, no positions, no open orders. Market was closed; next open 2026-11-17 9:30am New York.

- Step 8 (optional first trade): skipped 2026-11-16; the user went straight to the Part 2 rulebook prompt. Part 1 complete.

## Part 2: the rulebook (done 2026-11-16)

- Written: stocks.txt (30 tickers), rules.md (entry "none yet", mode alert), log.md, CLAUDE.md (the five standing instructions plus the bracket-order and daily-limit lines).
- **Next: Part 3 (find a strategy and test it).** User has been asked whether to carry on. First question there: do they have their own strategy, or should Fable suggest three to test? Backtest starting amount: $10,000 (matches the account).

## Part 6: make it run on its own (in progress)

- 2026-11-16: user chose **option A (Claude cloud scheduled tasks)**. Asked for a yes to add the allow rules to .claude/settings.json; waiting. All 15 alpaca tool names in setup.md's allow list were checked against the connected server and exist as written.
- 2026-11-16: the user answered the allow-rules question with "Wait, no. We're going to bring this into a Github Repo for the scheduled task. Then we'll need a webhook to link in Telegram for a way to gain my approval". So: allow rules NOT added and not approved yet (ask again later; unattended runs need them). The user wants GitHub + cloud tasks AND approval through Telegram. setup.md says Telegram replies need option B or C; with cloud runs nothing is listening. Options put to the user (my proposals, not from setup.md): (1) a second scheduled cloud task about 9:17am NY that reads the user's Telegram reply with getUpdates and places the waiting trades if it finds "Take it." from their chat ID; (2) a real webhook, which needs a small always-on relay outside Claude; (3) Telegram for alerts only, approve in the run. Waiting for their choice.
- 2026-11-16: user chose **(1) the scheduled check**. Built: notify.py (sends, prints `message_id=N`), check_approval.py (prints only APPROVED / NOT APPROVED; needs `--after-message-id N`; only the user's own chat ID counts; never prints message text), jobs/approve.md (5th job), and two new lines in CLAUDE.md (python vs python3; Telegram message id goes in log.md under "Waiting for approval"). Both scripts fail cleanly while the Telegram settings are missing; neither has been tested against real Telegram yet.
- Cloud portability fixes DONE: .mcp.json now uses the local `.venv-alpaca` exe if it exists, else `uvx alpaca-mcp-server` (the local path was tested; the new file only takes effect here in a new session, and the app may ask to approve the `alpaca` server again). scanner.md says python3, or python on Windows. `.venv-alpaca/` is already in .gitignore.
- `gh` (GitHub CLI) is NOT installed; git 2.54 is. No git repo in the folder yet.
- STILL TO DO for option A, in order, one question at a time:
  1. Allow rules in .claude/settings.json: DONE 2026-11-16 with the user's yes (question 2, the plan, has been asked; waiting). Used setup.md's list plus `Bash(python scan.py *)`, `Bash(python scan.py)`, `Bash(python3 notify.py *)`, `Bash(python notify.py *)`, `Bash(python3 check_approval.py *)`, `Bash(python check_approval.py *)`.
  2. Plan: ANSWERED 2026-11-16: the user is on **Pro** and chose **Opus 5.5 for all five scheduled tasks** (not Fable). The scanner sub-agent stays on Sonnet.
  3a. Local git repo: `git init -b main` done 2026-11-16. Checked: .env, prices.csv and .venv-alpaca are ignored; 23 files would be committed. NOT committed yet: git user.name/user.email are not set on this PC. Plan: when the user gives the repo URL, set (for this repo only) user.name to their GitHub username and user.email to `<username>@users.noreply.github.com`, commit, add the remote, push (Git Credential Manager will open a browser sign-in for the user). The user has been asked to create an empty PRIVATE repo on github.com and paste its URL.
  3. GitHub: user creates an empty PRIVATE repo on github.com (or agrees to install gh). Then `git init`, check `git check-ignore .env`, commit, push. Don't commit .env or prices.csv.
  3b. GitHub repo: https://github.com/Daniel-MidHaven/TradeDesk (private). Local commit 582ac53 made (author Daniel-MidHaven, GitHub noreply email, set for this repo only); remote `origin` added. Git here needs `-c credential.helper= -c credential.helper=manager` to sign in (the default helper never opens a window); the user signed in on 2026-11-16 and fetch works. FOUND: the user had already uploaded the folder through the website (commit 44758d5 "Add files via upload"): 20 files inside a subfolder `Claude_TradeDesk/`, identical to the local ones, plus prices.csv; no .env there (checked). Missing on GitHub: `.claude/` (settings + scanner), `.mcp.json`, `.gitignore`, and everything must be at the repo ROOT for cloud runs. Proposed to the user, waiting for a yes: merge the two histories (`git merge origin/main --allow-unrelated-histories`), remove the `Claude_TradeDesk/` subfolder copy (including prices.csv) in that merge, push to main. No force push; their upload stays in the history.
  3c. 2026-11-16: user said "Yes push it", but the push did NOT happen: GitHub now answers "Repository not found" for Daniel-MidHaven/TradeDesk, although the sign-in manager still holds the Daniel-MidHaven account and the repo was readable minutes earlier. Most likely the repo was deleted, renamed or recreated on the website (my guess). Asked the user what the repo is called now. If it comes back EMPTY: just `git push -u origin main` (no merge needed; update the remote URL if the name changed). If it has an upload again: fetch, compare, and use the merge plan in 3b. Local commit 582ac53 is intact.
  3d. PUSHED 2026-11-16. The user recreated the repo (same name) with only a README; merged it and pushed. GitHub main now has the 23 desk files at the top level plus README.md; no .env, prices.csv or .venv-alpaca. This repo's git config now uses the `manager` credential helper, so plain `git push` / `git pull` work. Changes made after this note (including this file) may still need a commit and push.
  3e. Two Telegram placeholder lines (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID) were appended to .env with printf, without reading the file. The user has been asked to create the bot and fill them in (step 4). When they say it's done, test with `python notify.py "..."`, then have them reply "Take it." and test `python check_approval.py --after-message-id N`.
  3f. 2026-11-16: the user filled in the Telegram lines. `python notify.py` sent a test message (message_id=3). The user has been asked to reply "Take it." in Telegram; when they say they have, run `python check_approval.py --after-message-id 3` and expect APPROVED (before the reply it should print NOT APPROVED).
  3g. 2026-11-16: Telegram fully TESTED from this PC: after the user replied "Take it.", check_approval.py printed APPROVED for id 3 and NOT APPROVED for a later id. Step 4 below is done. NEXT is step 5 (the user creates the cloud environment and connects GitHub at claude.ai/code; asked, waiting), then step 6 (five tasks on Opus 5.5; try creating them for the user with the `schedule` skill before asking them to click through the UI).
  4. (DONE) Telegram: user creates a bot with @BotFather, gets their user ID from @userinfobot, sends the bot one message. Token and ID go into the cloud environment's variables (and optionally .env here via the printf command in setup.md Part 7), typed by the user, never in chat.
  5. Cloud environment (user does this at claude.ai/code): network Custom with `paper-api.alpaca.markets`, `data.alpaca.markets`, `api.telegram.org`, plus the default package-manager list; variables ALPACA_API_KEY, ALPACA_SECRET_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
  6. Five tasks (all weekdays, New York time; each prompt ends with the commit-and-push sentence from setup.md step A4 and the Telegram summary sentence from Part 7):
     Morning `CRON_TZ=America/New_York 37 8 * * 1-5`; Approve `CRON_TZ=America/New_York 17 9 * * 1-5` with prompt "Run jobs/approve.md. If today isn't a trading day, do nothing."; Post-open `7 10`; Close `37 15`; Review `37 16 * * 5`.
  7. Run now on the morning task to test; then Part 8 (replay), then Finish.
- Old list, now handled above. Things to fix for the cloud BEFORE pushing to GitHub (cloud runs are Linux, this PC is Windows):
  1. `.mcp.json` currently hard-codes `C:/Users/Coolk/.../.venv-alpaca/Scripts/alpaca-mcp-server.exe`. Make it use that exe only if it exists, otherwise `exec uvx alpaca-mcp-server`, so one file works here and in the cloud. Takes effect here only in a new session; keep the Windows path working.
  2. `python` vs `python3`: Linux has `python3`. Allow both `Bash(python scan.py *)` and `Bash(python3 scan.py *)` (and the bare forms), and make scanner.md say to use python3, or python if python3 isn't available.
  3. Add `.venv-alpaca/` to .gitignore (also trades.csv / equity_curves.png are fine to commit; prices.csv is already ignored).
  4. No git repo yet in the folder; check `gh` is installed/signed in, else walk through github.com. Check `git check-ignore .env` before the first commit.
- Earlier: Still to ask, one at a time, before scheduling anything: (1) a yes to add the allow rules to .claude/settings.json (use `python scan.py`, not python3, and check tool names against the alpaca server), (2) which Claude plan they are on (Fable vs Opus for the scheduled runs).
- Mode is alert, so on a schedule the user must reply "Take it." to the morning run before 9:30am New York, or set up Telegram (Part 7, options B/C only).

## Part 5: alert or auto (done 2026-11-16: FINAL ANSWER IS ALERT)

- The user first switched to auto, then switched back to alert before any run. rules.md says alert. The entries below are the history.

- 2026-11-16: user chose AUTO. Paper account re-confirmed (PA number, $10,000), Mode line in rules.md now says auto, logged.
- The user has been offered one more morning run in auto and warned it would place the qualifying trades (as of the 16 Nov close: KO 20, PG 11, COST 1, PEP 13) as bracket orders for the 17 Nov open without a further question. Run it ONLY if they say yes; an old yes does not carry to a later day or session. Then Part 6 (scheduling): ask which option (A cloud, B this computer left on, C server, D other agent) and which Claude plan before scheduling.

## Part 4: the scanner and the daily jobs (done 2026-11-16; user skipped the four test trades, nothing placed)

- Done 2026-11-16: scan.py (`--live` or `--date`; both gave the same table for 2026-11-16), `.claude/agents/scanner.md` (says `python scan.py --live`, not python3), and jobs/morning.md, postopen.md, close.md, review.md, word for word from setup.md.
- The scanner sub-agent only loads in a NEW session; in the session that created it, the main session ran scan.py and the news itself.
- Morning job test run done in alert mode (evening of 2026-11-16, market closed): 4 trades proposed and written to log.md under "Waiting for approval": KO 20, PG 11, COST 1, PEP 13 shares. Nothing placed. The user was told "Take it." places them as bracket orders (market buy, gtc, stop and target attached) for the open on 2026-11-17; approval only counts before that open.
- **Next:** if the user says "Take it.", show/confirm and place the four bracket orders, then log them. Either way, then explain the four jobs are in place and ask whether to carry on to Part 5 (alert or auto).

## Part 3: find a strategy and test it (done 2026-11-16)

- User chose the breakout. Entry line written into rules.md (with the six-month-gain tie-break). Rulebook explained line by line.
- **Next: Part 4 (the scanner and the daily jobs).** User has been asked whether to carry on. Remember `python`, not `python3`, in scanner.md and anywhere else.

History of this part:

- 2026-11-16: user chose "Fable suggests three" (ran Miles's prompt). Three candidates proposed, all signalled on the daily close, bought at the next open, with the stop/target/time limit from rules.md and no second position in a stock already held:
  1. Breakout: close above the highest close of the previous 55 trading days (today not included) AND close above the 200-day simple average.
  2. Pullback: close above the 200-day simple average AND RSI(2) below 10.
  3. Oversold bounce: RSI(14) below 30.
- Done 2026-11-16: get_prices.py, signals.py, backtest.py written. prices.csv downloaded (31 tickers, 1,566 days each, 2020-08-24 to 2026-11-16, SIP feed, no gaps). backtest.py needs no pandas; it only needs matplotlib for the chart and skips the chart if it's missing. Ranking when too many qualify: biggest six-month (126-day) gain first, already used in the test.
- Five-year results (2021-11-16 to 2026-11-16, $10,000), run with plain `python backtest.py`: Breakout $19,499 (+95.0%, max drawdown -16.9%, Sharpe 0.95, 378 trades, 45% wins); Pullback $13,347 (+33.5%, -26.6%, 0.43, 359, 42%); Bounce $16,669 (+66.7%, -14.5%, 0.71, 236, 47%); SPY $16,928 (+69.3%, -24.5%, 0.69); all 30 stocks $20,782 (+107.8%, -19.9%, 0.98). Results shown and explained to the user.
- Chart done 2026-11-16: `uv run --with matplotlib` fails on this PC ("file is being used by another process", see notes below), so with the user's yes matplotlib was pip-installed into `.venv-alpaca/`. Run the backtest (and the Part 8 replay) with `.venv-alpaca\Scripts\python.exe backtest.py`. equity_curves.png saved.
- **Next:** user has been asked which strategy goes into the rulebook. On the answer: which strategy goes into the rulebook (Miles's choice: breakout), then write the Entry line in rules.md. The Entry line must contain the word "breakout", "pullback" or "bounce" so signals.entry_rule_name() can find it, and should include the six-month-gain ranking.

Answers to the six Part 2 questions:

- User ran the rules.md prompt on 2026-11-16. Ask the six questions one at a time; answers so far are listed below.
- Q1 stocks: Miles's 30 (AAPL, ABBV, AMZN, AVGO, BAC, CAT, COST, CRM, CSCO, CVX, DIS, GOOGL, HD, JNJ, JPM, KO, MA, MCD, META, MRK, MSFT, NVDA, ORCL, PEP, PG, TSLA, UNH, V, WMT, XOM).
- Q2 size per trade: 20% of the account, whole shares.
- Q3 max positions: 5.
- Q4 daily loss limit: 3%.
- Q5 stop and target: stop 2 x ATR(14) below the entry price, target 4 x ATR(14) above it.
- Q6 time limit: sell at the open after 30 trading days.

## Notes for this computer (Windows)

- `python3` is not a working command here. Use `python` wherever setup.md says `python3` (scripts, scanner.md, allow rules, job prompts).
- The `claude` terminal command is not installed; the user works in the desktop app.
- `uvx alpaca-mcp-server` does not work on this PC (2026-11-16): uv fails installing `pywin32` with "file is being used by another process" every time, probably Trend Micro Antivirus+ scanning the files mid-install (my guess, not confirmed). Do not change antivirus settings. Workaround in place: the server is pip-installed in `.venv-alpaca/` in the desk folder, and `.mcp.json` runs `.venv-alpaca/Scripts/alpaca-mcp-server.exe` instead of `uvx`. `--help` works; a real connection with the user's keys is still untested (needs a new session). To update the server: `.venv-alpaca\Scripts\python.exe -m pip install -U alpaca-mcp-server`.
- Claude cannot access `.env` in this folder at all (blocked by permissions, as intended), so it cannot check whether the keys are filled in; ask the user.
