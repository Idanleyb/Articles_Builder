# Articles_Builder
Agent for creating Fintech / Music and Marketing articles based on new innovations and ideas in the market. 
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
| `requirements.txt` | Python dependencies |
| `.github/workflows/daily_run.yml` | Runs the pipeline daily via GitHub Actions |

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
