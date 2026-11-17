"""notify.py: sends a message to your Telegram from the desk's bot.

Run it with:  python3 notify.py "the text to send"
         or:  echo "the text" | python3 notify.py
(On Windows, use python instead of python3.)

It reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from the environment, or from
.env, and never prints them. It prints the id of the message it sent, which the
morning job writes into log.md so the approval check knows where to start.
It uses only Python's standard library.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def read_setting(name):
    """A value from the environment, or from .env if it isn't there."""
    value = os.environ.get(name)
    env_path = os.path.join(HERE, ".env")
    if not value and os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                key, _, text = line.strip().partition("=")
                if key.strip() == name:
                    value = text.strip().strip('"').strip("'")
    if not value or value.startswith("paste-your"):
        sys.exit(f"{name} is not set. Add it to .env, or to the cloud environment's variables.")
    return value


def telegram(method, params):
    """Call one Telegram bot method and return its result."""
    token = read_setting("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = urllib.parse.urlencode(params).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        # The address contains the token, so only the error code and Telegram's text are shown.
        sys.exit(f"Telegram returned error {error.code}: {error.read().decode('utf-8', 'replace')[:200]}")
    except urllib.error.URLError as error:
        sys.exit(f"Could not reach Telegram: {error.reason}")
    if not payload.get("ok"):
        sys.exit(f"Telegram refused the request: {payload.get('description')}")
    return payload["result"]


def main():
    text = " ".join(sys.argv[1:]).strip() or sys.stdin.read().strip()
    if not text:
        sys.exit('Nothing to send. Usage: python3 notify.py "the text to send"')
    # Telegram's limit is 4096 characters a message.
    result = telegram("sendMessage", {"chat_id": read_setting("TELEGRAM_CHAT_ID"), "text": text[:4000]})
    print(f"Sent. message_id={result['message_id']}")


if __name__ == "__main__":
    main()
