# RotoWire EuroLeague Injury Watcher → Slack

Checks https://www.rotowire.com/euro/news.php?view=injuries every 30 minutes
and posts any new entries to a Slack channel.

## 1. Get a Slack Incoming Webhook URL

1. Go to https://api.slack.com/apps → **Create New App** → **From scratch**.
2. Name it (e.g. "RotoWire Injury Bot") and pick your workspace.
3. In the app settings, go to **Incoming Webhooks** → toggle **On**.
4. Click **Add New Webhook to Workspace**, choose the channel to post in, and authorize.
5. Copy the webhook URL (looks like `https://hooks.slack.com/services/T000/B000/xxxxxxxx`).
   Keep this private — anyone with it can post to that channel.

## 2. Create a GitHub repo

1. Create a new **private** GitHub repo (public is fine too, but private keeps things tidier).
2. Push these three files/folders into it:
   - `watch_injuries.py`
   - `.github/workflows/watch.yml`
   - `seen_injuries.json`

## 3. Add the webhook as a secret

1. In the repo: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.
2. Name: `SLACK_WEBHOOK_URL`
3. Value: paste the webhook URL from step 1.

## 4. Avoid a flood of notifications on first run

The included `seen_injuries.json` starts empty, which means the very first run
would treat every item currently on the page as "new" and post them all to
Slack at once. To avoid that:

- **Option A (recommended):** Before enabling the schedule, run the script
  once locally (`pip install requests beautifulsoup4 && python watch_injuries.py`)
  *without* setting `SLACK_WEBHOOK_URL`, then manually copy the resulting
  `seen_injuries.json` (it'll populate with current items even if the Slack
  post fails/is skipped — you can also temporarily comment out the
  `notify_slack` call) and commit that as your starting state.
- **Option B (simpler, less precise):** Just let the first run post everything
  once as a "backfill," then it'll be quiet after that and only post new items.

## 5. Test it

- Go to the repo's **Actions** tab → select **RotoWire Injury Watcher** →
  **Run workflow** to trigger it manually and confirm it posts to Slack correctly.

## Notes / caveats

- This scrapes RotoWire's HTML rather than using an official API/RSS feed
  (RotoWire doesn't appear to publish one for this page), so if they change
  their page layout, the parsing logic in `fetch_items()` may need updating.
- The schedule runs every 30 minutes; GitHub's cron scheduler can lag by a
  few minutes under load, so treat it as "roughly every 30 min," not exact.
- If nothing gets posted and you suspect the page layout changed, run the
  workflow manually and check the Action's logs — it prints a warning if it
  can't parse any items at all.
