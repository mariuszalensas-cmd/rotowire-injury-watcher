"""
Watches the RotoWire EuroLeague injuries page for new entries and
posts any new ones to a Slack channel via an Incoming Webhook.

State (which items have already been posted) is kept in seen_injuries.json,
which the GitHub Actions workflow commits back to the repo after each run.
"""

import os
import re
import json
import sys
import requests
from bs4 import BeautifulSoup

URL = "https://www.rotowire.com/euro/news.php?view=injuries"
STATE_FILE = os.path.join(os.path.dirname(__file__), "seen_injuries.json")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL")  # e.g. "#injury-alerts" or "C0123456789"

DATE_RE = re.compile(
    r"(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{1,2},\s+\d{4}"
)


def fetch_items():
    """Fetch the page and return a list of dicts, one per news item."""
    resp = requests.get(
        URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; injury-watcher/1.0)"},
        timeout=20,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    items = []
    seen_container_ids = set()

    # Each news entry links to a player's page (/euro/player/...).
    # We walk up from that link until we find a container whose text
    # includes a date, which reliably scopes one news item.
    for link in soup.select('a[href*="/euro/player/"]'):
        container = link
        for _ in range(6):
            if container.parent is None:
                break
            container = container.parent
            if DATE_RE.search(container.get_text(" ", strip=True)):
                break

        cid = id(container)
        if cid in seen_container_ids:
            continue
        seen_container_ids.add(cid)

        text = container.get_text(" ", strip=True)
        date_match = DATE_RE.search(text)
        date_str = date_match.group(0) if date_match else ""
        player_name = link.get_text(strip=True)

        if not player_name or not date_str:
            # Didn't find a clean item; skip rather than risk false positives
            continue

        href = link.get("href", "")
        uid = f"{href}|{date_str}|{player_name}"

        items.append(
            {
                "id": uid,
                "player": player_name,
                "url": "https://www.rotowire.com" + href,
                "date": date_str,
                "text": text,
            }
        )

    return items


def load_seen():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(seen), f, indent=2)


def notify_slack(item):
    snippet = item["text"]
    if len(snippet) > 400:
        snippet = snippet[:400].rsplit(" ", 1)[0] + "..."

    payload = {
        "channel": SLACK_CHANNEL,
        "text": (
            f"*New EuroLeague injury update:* <{item['url']}|{item['player']}> "
            f"— {item['date']}\n{snippet}"
        ),
    }
    resp = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        # Slack returns 200 OK even on logical failures (e.g. bad channel,
        # missing scope, bot not invited to channel) — surface those here.
        raise RuntimeError(f"Slack API error: {data.get('error')}")


def main():
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL:
        print(
            "ERROR: SLACK_BOT_TOKEN and/or SLACK_CHANNEL environment variables are not set.",
            file=sys.stderr,
        )
        sys.exit(1)

    seen = load_seen()
    items = fetch_items()

    if not items:
        print("Warning: no items parsed from page. Site structure may have changed.")
        return

    new_items = [i for i in items if i["id"] not in seen]

    if not new_items:
        print(f"No new items. ({len(items)} items on page, all already seen.)")
        return

    for item in new_items:
        try:
            notify_slack(item)
            print(f"Notified Slack: {item['player']} ({item['date']})")
            seen.add(item["id"])
        except Exception as e:
            print(f"Failed to notify Slack for {item['player']}: {e}", file=sys.stderr)

    save_seen(seen)


if __name__ == "__main__":
    main()
