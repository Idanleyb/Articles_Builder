# Signal Tracker

A daily pipeline that scans Music, Fintech, and AI Marketing & Growth for new
products and ideas, scores them, and flags the strongest ones as article
candidates — feeding a downstream article-writing workflow (SEO/GEO).

## How it works

```
RSS feeds ─┐
           ├─→ fetch_and_score.py ─→ Claude (classify + score) ─→ data.json ─→ dashboard.html
Product Hunt API ─┘
```

Every item gets:
- **Vertical**: Music / Fintech / AI Marketing & Growth
- **Category**: Content AI / Analytics & Insights / Automation & Workflow / Other-Emerging
- A short description and an "innovation" note (what's actually new here)
- Engagement numbers where available (Product Hunt votes/comments; RSS items get a neutral default — see caveat below)
- A weighted score, 0–100
- An `article_worthy` flag (score ≥ 75)

The dashboard reads the results, lets you filter/sort, and lists every
article-worthy item in a queue grouped by vertical — ready to copy into your
article-writing skill.

## Files

| File | Purpose |
|---|---|
| `fetch_and_score.py` | Daily pipeline: fetch → classify → score → write `data.json` |
| `generate_sample_data.py` | Produces placeholder `data.json` for testing the dashboard without API keys |
| `dashboard.html` | The web app — open directly in a browser |
| `write_articles.py` | Monday/Wednesday pipeline: select item(s) → generate article via the tone guide → append to Google Doc |
| `selected_for_writing.json` | Edit this before a run to hand-pick which item(s) to write about; leave empty for auto-pick |
| `written_log.json` | Auto-maintained record of what's already been written about (prevents repeats) |
| `requirements.txt` | Python dependencies |
| `.github/workflows/daily_run.yml` | Runs the tracker pipeline daily |
| `.github/workflows/writer_run.yml` | Runs the article writer every Monday and Wednesday |

## Article Writer (twice-weekly)

Every Monday and Wednesday, `write_articles.py`:
1. Reads `selected_for_writing.json` — if you've pasted item name(s) from the
   dashboard's Article Queue in there, those are used. Otherwise it falls back
   to the single highest-scoring item that hasn't already appeared in
   `written_log.json` — this fallback is **not** gated on the 75+ article-worthy
   threshold, so a run never comes up empty just because no item cleared that
   bar; the threshold remains purely a quality signal on the dashboard.
2. Generates the article using the tone/voice rules from the `article-writer`
   skill (technical-marketer lens, musician's mindset, no hype, LinkedIn
   formatting, SEO in the opening lines, GEO-friendly clear claims).
3. Appends the finished article to a shared Google Doc, with a date/source
   header so multiple articles stack cleanly over time.
4. Logs what was written and clears the selection file.

### Additional secrets needed

| Secret | Required | Notes |
|---|---|---|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Yes | Full contents of the service account's downloaded JSON key |
| `GOOGLE_DOC_ID` | Yes | The ID from the doc's URL: `docs.google.com/document/d/THIS_PART/edit` |

### One-time Google Cloud setup
1. **console.cloud.google.com** → create or select a project
2. Enable the **Google Docs API** and **Google Drive API**
3. **IAM & Admin → Service Accounts → Create Service Account**
4. On the new service account, **Keys → Add Key → Create new key → JSON** — downloads a `.json` file
5. Create (or pick) the Google Doc articles should land in, click **Share**,
   and share it with the service account's email (looks like
   `name@project-id.iam.gserviceaccount.com`) with **Editor** access
6. Copy the entire downloaded JSON file's contents into the
   `GOOGLE_SERVICE_ACCOUNT_JSON` secret, and the doc's ID into `GOOGLE_DOC_ID`

### Picking what gets written about
Open `selected_for_writing.json`, add the exact `name` value(s) from the
dashboard's Article Queue to `selected_names`, and commit before Monday/Wednesday's
scheduled run (or trigger the workflow manually via **Actions → Monday/Wednesday
Article Writer → Run workflow** right after selecting).

## Scoring weights

| Factor | Weight |
|---|---|
| Relevance to the 3 verticals | 40% |
| Engagement | 30% |
| Novelty | 20% |
| Applicability (to your own products) | 10% |

Adjust these in the `WEIGHTS` dict at the top of `fetch_and_score.py`. The
article-worthy cutoff (`ARTICLE_WORTHY_THRESHOLD`) lives in the same file.

## Setup

### 1. Create the repo
Create a new GitHub repo and add all files from this package, keeping
`daily_run.yml` under `.github/workflows/`.

### 2. Add secrets
In **Settings → Secrets and variables → Actions**, add:

| Secret | Required | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Used to classify and score each item |
| `PRODUCT_HUNT_TOKEN` | No | Enables the Product Hunt source; without it, RSS-only |

Never commit keys directly to the repo — secrets only.

### 3. Enable GitHub Pages
**Settings → Pages** → deploy from your default branch, so `dashboard.html`
is viewable at a public URL after each run.

### 4. Point the dashboard at live data
`dashboard.html` currently ships with sample data embedded directly in the
`<script>` tag (`const DATA = [...]`). Once `fetch_and_score.py` has run at
least once and produced a real `data.json`, replace that line with:

```js
let DATA = [];
fetch('data.json').then(r => r.json()).then(d => { DATA = d; render(); renderQueue(); });
```

### 5. Test locally before relying on the daily run
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
export PRODUCT_HUNT_TOKEN=your_token_here   # optional
python fetch_and_score.py
```
Check the printed summary (`Scored N relevant items`, `Article-worthy: N`)
and inspect `data.json` before turning on the schedule.

### 6. Turn on the schedule
Once `data.json` looks right, the GitHub Actions workflow takes over —
runs daily at 06:00 UTC, regenerates `data.json`, and commits it back to
the repo automatically. You can also trigger it manually from the Actions
tab (`workflow_dispatch`).

## Known limitations

- **RSS items have no real engagement data.** LinkedIn-style like/comment/share
  counts aren't available through compliant sources, so RSS-sourced items get
  a neutral engagement score (40) rather than a fabricated number. Only
  Product Hunt items get genuine engagement-based scoring.
- **LinkedIn is intentionally excluded.** Its Terms of Service prohibit
  automated scraping of posts/engagement data, so this pipeline sources from
  RSS feeds and Product Hunt's official API instead. If you want to fold in
  posts you personally see on LinkedIn, paste them in manually — no
  automation involved.
- **RSS source list is a starting point.** Add or swap feeds in the
  `RSS_FEEDS` list in `fetch_and_score.py` as you find better ones per
  vertical.

## Next step

Article-worthy items in the queue are meant to be handed to a future
article-writing skill (SEO + GEO optimized). Each queue entry carries the
name, vertical, and innovation summary needed to brief that skill.
