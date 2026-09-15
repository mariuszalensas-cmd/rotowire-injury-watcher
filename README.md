# RotoWire EuroLeague Injury Watcher → Slack

Checks https://www.rotowire.com/euro/news.php?view=injuries every 30 minutes
and posts any new entries to a Slack channel.

## 1. Slack bot setup

This version uses a Slack bot token (`xoxb-...`) with the `chat:write` scope,
via Slack's `chat.postMessage` API, rather than an incoming webhook.

1. Make sure your Slack app has the **`chat:write`** OAuth scope
   (**OAuth & Permissions** → **Scopes** → **Bot Token Scopes**).
2. Reinstall the app to your workspace if you added the scope after installing.
3. Copy the **Bot User OAuth Token** (starts with `xoxb-`) from **OAuth & Permissions**.
4. Invite the bot to the channel you want it posting in:
   in Slack, go to that channel and type `/invite @YourBotName`.
5. Note the channel name (e.g. `#injury-alerts`) or channel ID (e.g. `C0123456789`) —
   you'll need it in step 3 below.

## 2. Create a GitHub repo

1. Create a new **private** GitHub repo (public is fine too, but private keeps things tidier).
2. Push these three files/folders into it:
   - `watch_injuries.py`
   - `.github/workflows/watch.yml`
   - `seen_injuries.json`

## 3. Add two repository secrets

In the repo: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.
Add both of these:

1. Name: `SLACK_BOT_TOKEN` → Value: your `xoxb-...` bot token from step 1.
2. Name: `SLACK_CHANNEL` → Value: the channel name (e.g. `#injury-alerts`) or channel ID
   (e.g. `C0123456789`) from step 1. Channel ID is more reliable — you can find it
   at the bottom of a channel's "About" section in Slack.

## 4. Avoid a flood of notifications on first run

The included `seen_injuries.json` starts empty, which means the very first run
would treat every item currently on the page as "new" and post them all to
Slack at once. To avoid that:

- **Option A (recommended):** Before enabling the schedule, run the script
  once locally (`pip install requests beautifulsoup4 && python watch_injuries.py`)
  *without* setting `SLACK_BOT_TOKEN`/`SLACK_CHANNEL`, then manually copy the
  resulting `seen_injuries.json` (it'll populate with current items even
  though the Slack post itself will fail/be skipped without those env vars
  set) and commit that as your starting state.
- **Option B (simpler, less precise):** Just let the first run post everything
  once as a "backfill," then it'll be quiet after that and only post new items.

## 5. Test it

- Go to the repo's **Actions** tab → select **RotoWire Injury Watcher** →
  **Run workflow** to trigger it manually and confirm it posts to Slack correctly.

## Notes / caveats

- This scrapes RotoWire's HTML rather than using an official API/RSS feed
  (RotoWire doesn't appear to publish one for this page), so if they change
  their page layout, the parsing logic in `fetch_items()` may need updating.
- The schedule is set to run **every minute**. Two things to know about that:
  - GitHub's cron scheduler can lag by a few minutes under load — "every
    minute" means "as close to every minute as GitHub allows," not a
    guaranteed exact interval.
  - GitHub automatically **disables scheduled workflows in a repo that's
    been inactive for 60 days** (no pushes/commits). If notifications
    suddenly stop, check the Actions tab — you may just need to re-enable it.
  - Running every minute uses a lot more of your GitHub Actions minutes than
    a longer interval. Free/personal accounts get a monthly quota of
    Actions minutes; each run of this workflow takes maybe 10-20 seconds,
    so per-minute checks add up over a month. If you hit limits, dial the
    cron back to e.g. `*/5 * * * *` (every 5 minutes).
- If nothing gets posted and you suspect the page layout changed, run the
  workflow manually and check the Action's logs — it prints a warning if it
  can't parse any items at all.
