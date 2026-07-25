# NEET Counselling Auto-Monitor

Watches ~130 NEET counselling websites every 30 minutes. Sends Telegram alerts the moment something meaningful changes on **priority sites** (MCC, AACCC, NMC, NBE, NTA, UP/Rajasthan/Gujarat/MP/Bihar/Maharashtra). Batches the rest into one **daily email digest**.

Runs on GitHub Actions — **free**, no server to manage.

---

## ⚠️ Read this first — realistic expectations

I want to be straight with you before you invest time:

1. **This will not be 100% reliable, and no system watching 138 government websites can be.** Government sites in India go down, block automated traffic (Cloudflare, WAFs), post as images or PDFs, and change their HTML without warning. Expect **some sites to fail every run** — that's normal. The dashboard shows which ones.
2. **~30 sites use heavy JavaScript** (e.g. `admissions.nic.in` portals) — this version won't fully read them. It will detect *that they exist* but might miss content changes. Adding JS support (Playwright) is doable but ~3× more setup — save it for later if you find you're missing alerts.
3. **The MCC and NMC sites specifically use aggressive Cloudflare bot protection.** They *may* work from GitHub Actions IPs (Azure datacenter reputation is decent), or they *may* return 403. If they 403 consistently, the fallback is Distill.io (I mention it below) for just those 2–3 sites.
4. **You'll get some false alarms in the first 1–2 weeks** while the baseline snapshots settle. After that it quiets down.

Take this as a very good **first line of defense**, not a guarantee.

---

## What you'll need (all free)

- A GitHub account
- A Telegram account
- A Gmail account (for email digests)
- 30–45 minutes for first-time setup

---

## Setup — Step by step

### Part 1 — Get the code into GitHub (10 min)

1. Go to [github.com/new](https://github.com/new). Create a new repository:
   - Name: `neet-monitor` (or anything you want)
   - **Private** repository (recommended — snapshots are stored inside)
   - Do **not** initialize with README
   - Click **Create repository**
2. Download this project as a ZIP and extract it on your computer.
3. Upload the files:
   - On the new repo page, click **"uploading an existing file"**
   - Drag *everything* from the extracted folder (including the hidden `.github/` folder — see note below)
   - Commit message: "initial setup"
   - Click **Commit changes**

   > **Important — hidden folders on Mac/Windows:** the `.github` folder starts with a dot, so it's hidden by default.
   > - **Mac:** in Finder press `Cmd + Shift + .` to show hidden files
   > - **Windows:** in File Explorer → View → tick "Hidden items"
   > 
   > You must upload `.github/workflows/monitor.yml` or the scheduler won't run.

4. Verify: your repo should show `monitor/`, `websites.csv`, `requirements.txt`, and `.github/workflows/monitor.yml` in the file list.

### Part 2 — Telegram bot (5 min)

1. Open Telegram, search for **@BotFather**, tap Start.
2. Send `/newbot`. Give it any name and username (must end in `bot`, e.g. `my_neet_alerts_bot`).
3. BotFather replies with a token like `123456789:ABCdef...`. **Copy it** — this is your `TELEGRAM_BOT_TOKEN`.
4. Search for your new bot in Telegram and send it any message (e.g. "hi"). This creates the chat.
5. Open this URL in a browser (paste your token in place of `<TOKEN>`):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
6. In the JSON response find `"chat":{"id":123456789, ...}`. That number is your `TELEGRAM_CHAT_ID`.

### Part 3 — Gmail app password (10 min)

Gmail won't accept your normal password from scripts. You need an **App Password**:

1. Turn on 2-Step Verification: [myaccount.google.com/security](https://myaccount.google.com/security) → 2-Step Verification → follow prompts.
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. App name: "NEET Monitor" → **Create**.
4. Google shows a 16-character password (like `abcd efgh ijkl mnop`). **Copy it, remove the spaces**. This is your `SMTP_PASSWORD`.
5. `SMTP_USER` and `EMAIL_FROM` = your full Gmail address.
6. `EMAIL_TO` = where you want digest emails (can be same address).

### Part 4 — Add secrets to GitHub (5 min)

1. In your GitHub repo → **Settings** (top nav) → **Secrets and variables** → **Actions**.
2. Click **New repository secret**. Add these one at a time:

| Name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | from Part 2 step 3 |
| `TELEGRAM_CHAT_ID` | from Part 2 step 6 |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | your Gmail address |
| `SMTP_PASSWORD` | 16-char app password (no spaces) |
| `EMAIL_FROM` | your Gmail address |
| `EMAIL_TO` | where you want digest emails |

### Part 5 — Turn it on (2 min)

1. Go to the **Actions** tab of your repo.
2. If GitHub shows *"Workflows aren't being run"*, click **I understand my workflows, go ahead and enable them**.
3. Click **NEET Monitor** on the left → **Run workflow** button → **Run workflow**.
4. Wait ~5 minutes. Refresh. You should see a green ✓ (or a yellow spinner while running).
5. **First run does not send alerts** — it's just building baseline snapshots. Second run onwards is when you'll get real alerts.
6. After 30 min, a second run kicks off automatically. From then on it runs every 30 min forever.

### Part 6 — See what's happening (the dashboard)

After the first successful run, a dashboard file is generated at `data/dashboard.html`.

**Option A — quickest:** in GitHub, browse to `data/dashboard.html` → click **Raw** → save the page. Open the saved HTML file in your browser.

**Option B — always up-to-date link (5 min setup):** enable GitHub Pages.
1. Repo → Settings → Pages
2. Source: **Deploy from a branch** → Branch: `main` → Folder: `/ (root)` → Save
3. Wait 2 min, then visit `https://<your-github-username>.github.io/<repo-name>/data/dashboard.html`
4. The dashboard auto-updates whenever the workflow commits new state.

---

## What alerts look like

**Instant Telegram (HIGH priority sites):**
```
🔔 MCC
https://mcc.nic.in/

• [pdf_added] New PDF: https://mcc.nic.in/notices/round1-schedule.pdf
• [notice_text_added] New content: MCC has released Round 1 Registration Schedule…
```

**Daily digest email (MEDIUM/LOW priority sites)** — sent once a day at ~8:30 AM IST, grouped by site.

---

## When something goes wrong

**"I'm not getting any alerts"**
- Is the workflow running? Repo → Actions tab → should show recent runs.
- Did the first run finish OK? First run never sends alerts (it's the baseline).
- Check the dashboard "Failing sites" section — if MCC is in there, the site is being blocked from GitHub Actions and you should add it to Distill.io separately.
- Test Telegram manually: `curl "https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<CHATID>&text=test"` — if this doesn't send, your token/chat_id is wrong.

**"Too many alerts / noisy"**
- Edit `monitor/config.py` → `ALERT_KEYWORDS` list → remove any keyword that's giving false positives (e.g. remove "notice" if lots of pages have random "notice" text).
- Move sites from HIGH → MEDIUM in `websites.csv` to push them into the daily digest instead of instant.

**"A specific site keeps failing"**
- Check the dashboard's Failing sites table for the last error.
- HTTP 403 = the site blocks GitHub Actions. Options: (1) accept it and use Distill.io for that one site, (2) later, run a small VPS-based scraper for just that site.
- Timeouts = site is slow. Increase `REQUEST_TIMEOUT` in `.env.example` (but note: env vars in GitHub go in Secrets, not this file — add a secret `REQUEST_TIMEOUT` = `30`).
- HTTP 200 but no changes ever detected = probably a JS-heavy site. Log it and move on for now.

**"MCC / NMC keeps returning 403"**
This is expected for the most locked-down gov sites. Realistic fix: use [Distill.io](https://distill.io/) (free tier: 25 monitors) for just those 2–3 sites. Point-and-click, no code, and it sends to your Telegram/email too.

---

## Adding / removing sites

Edit `websites.csv` in GitHub directly (click the file → pencil icon → edit → commit). Columns:

- `state` — free-form
- `name` — displayed in alerts
- `url` — the URL to watch
- `priority` — `HIGH` (instant Telegram) / `MEDIUM` / `LOW` (daily digest)
- `category` — free-form label

Next run picks up your changes.

---

## Adjusting alert sensitivity

Edit `monitor/config.py`:

- `ALERT_KEYWORDS` — only changes matching one of these words trigger alerts. Add/remove to tune.
- `NOISE_PATTERNS` — regex patterns stripped before comparing. Add ones you see causing false alarms (e.g. a specific "Last updated at HH:MM" pattern from a site).
- `DIGEST_HOUR_UTC` — hour of day (UTC) when digest email fires. `3` = 8:30 AM IST.

Commit the change → next run uses it.

---

## Project layout

```
neet-monitor/
├── .github/workflows/monitor.yml   # runs every 30 min
├── monitor/
│   ├── main.py         # orchestrator
│   ├── config.py       # settings + keywords
│   ├── fetcher.py      # async HTTP with retry
│   ├── extractor.py    # HTML → structured snapshot
│   ├── differ.py       # snapshot diff + keyword gate
│   ├── storage.py      # SQLite history + JSON snapshots
│   ├── notifier.py     # Telegram + email
│   └── dashboard.py    # HTML dashboard generator
├── data/               # (auto-generated & committed by workflow)
│   ├── snapshots/      # per-site JSON
│   ├── history.db      # SQLite: runs, changes, dedupe
│   └── dashboard.html
├── websites.csv        # your site list
├── requirements.txt
├── .env.example        # local dev only; production uses GitHub Secrets
└── README.md
```

---

## Running locally (optional, for testing)

```bash
git clone https://github.com/<you>/neet-monitor.git
cd neet-monitor
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Telegram token + chat_id
python -m monitor.main
```

Open `data/dashboard.html` to see results.

---

## What's intentionally not in v1 (and why)

- **JS rendering (Playwright):** would work but triples setup complexity and pushes runtime past the free GitHub Actions budget. If a specific site matters and needs JS, easiest path is Distill.io for just that site.
- **OCR for image notices:** rare enough that adding Tesseract weighs down every run.
- **AI-written summaries:** costs money (OpenAI API). Current rule-based summaries are informative enough — you'll see "New PDF: round1-schedule.pdf" which is what you actually need.
- **WhatsApp alerts:** Meta's Cloud API requires pre-approved templates for automated alerts — you can't just send free-form text. Telegram gives you the same instant experience with zero friction.

If any of these become important once you're using it, they're modular additions — I can help you plug them in.
