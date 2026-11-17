"""check_approval.py: checks whether you replied "Take it." on Telegram.

Run it with:  python3 check_approval.py --after-message-id 123
(On Windows, use python instead of python3.)

The number is the id of the morning job's proposal message, from log.md. The
script looks at the messages your bot has received and prints exactly one line:

  APPROVED       you sent "Take it." after that proposal, in the last few hours
  NOT APPROVED   anything else

Only messages from your own Telegram account (TELEGRAM_CHAT_ID) count, and the
script never prints what a message says: a Telegram message can answer yes,
and nothing more. It uses only Python's standard library.
"""
import argparse
import re
import time

from notify import read_setting, telegram


def main():
    parser = argparse.ArgumentParser(description="Check Telegram for a 'Take it.' reply.")
    parser.add_argument("--after-message-id", type=int, required=True,
                        help="the id of the proposal message the morning job sent")
    parser.add_argument("--max-age-hours", type=float, default=3,
                        help="ignore replies older than this (default 3 hours)")
    args = parser.parse_args()

    owner = str(read_setting("TELEGRAM_CHAT_ID"))
    # Telegram keeps the messages a bot receives for 24 hours. Reading them
    # without an offset leaves them in place, so this can safely be run twice.
    updates = telegram("getUpdates", {"timeout": 0, "allowed_updates": '["message"]'})

    approved = False
    for update in updates:
        message = update.get("message") or {}
        sender = str((message.get("from") or {}).get("id", ""))
        chat = str((message.get("chat") or {}).get("id", ""))
        if sender != owner or chat != owner:
            continue  # not from you, in your own chat with the bot
        if message.get("message_id", 0) <= args.after_message_id:
            continue  # sent before this morning's proposal
        if time.time() - message.get("date", 0) > args.max_age_hours * 3600:
            continue  # too old
        words = re.sub(r"[^a-z ]", "", (message.get("text") or "").lower()).split()
        if words == ["take", "it"]:
            approved = True

    print("APPROVED" if approved else "NOT APPROVED")


if __name__ == "__main__":
    main()
