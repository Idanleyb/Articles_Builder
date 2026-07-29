"""
Daily fetch + score pipeline for the Signal Tracker (Music / Fintech / AI Marketing & Growth).

WHAT THIS DOES
1. Pulls candidate items from RSS feeds (no key needed) and Product Hunt (needs a token).
2. Sends each candidate to Claude to: classify vertical + category, write a short
   description + innovation summary, and score it against the weighted rubric.
3. Writes results to data.json in the same shape dashboard.html expects.

REQUIRED ENV VARS (set as GitHub Actions secrets, never hardcode):
  ANTHROPIC_API_KEY      - for classification/scoring
  PRODUCT_HUNT_TOKEN     - optional, enables the Product Hunt source

RUN LOCALLY:
  pip install anthropic feedparser requests
  export ANTHROPIC_API_KEY=...
  export PRODUCT_HUNT_TOKEN=...   # optional
  python fetch_and_score.py
"""
import json
import os
import re
from datetime import datetime, timezone

import feedparser
import requests
from anthropic import Anthropic

# ---- Configuration -----------------------------------------------------

RSS_FEEDS = [
    # AI Marketing & Growth
    "https://www.marketingaiinstitute.com/blog/rss.xml",
    "https://www.bensbites.co/feed",
    # Fintech
    "https://www.fintechbrainfood.com/feed",
    # Music
    "https://musically.com/feed/",
]

PRODUCT_HUNT_TOPICS = ["artificial-intelligence", "marketing", "fintech", "music"]

VERTICALS = ["Music", "Fintech", "AI Marketing & Growth"]
CATEGORIES = ["Content AI", "Analytics & Insights", "Automation & Workflow", "Other / Emerging"]

WEIGHTS = {"relevance": 0.40, "engagement": 0.30, "novelty": 0.20, "applicability": 0.10}
ARTICLE_WORTHY_THRESHOLD = 75
MAX_ITEMS_TO_SCORE = 40  # cap per run to control API cost

client = Anthropic()  # reads ANTHROPIC_API_KEY from env


# ---- Step 1: gather raw candidates -------------------------------------

def fetch_rss_items():
    items = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:
                items.append({
                    "raw_title": entry.get("title", ""),
                    "raw_text": re.sub("<[^<]+?>", "", entry.get("summary", ""))[:1200],
                    "url": entry.get("link", ""),
                    "source": feed.feed.get("title", url),
                    "likes": None, "comments": None, "shares": None,  # RSS has no engagement data
                })
        except Exception as e:
            print(f"[warn] RSS fetch failed for {url}: {e}")
    return items


def fetch_product_hunt_items():
    token = os.environ.get("PRODUCT_HUNT_TOKEN")
    if not token:
        print("[info] PRODUCT_HUNT_TOKEN not set, skipping Product Hunt source.")
        return []
    items = []
    query = """
    query($topic: String!) {
      posts(topic: $topic, order: VOTES, first: 10) {
        edges { node { name tagline description url votesCount commentsCount } }
      }
    }
    """
    for topic in PRODUCT_HUNT_TOPICS:
        try:
            resp = requests.post(
                "https://api.producthunt.com/v2/api/graphql",
                json={"query": query, "variables": {"topic": topic}},
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )
            resp.raise_for_status()
            edges = resp.json()["data"]["posts"]["edges"]
            for edge in edges:
                node = edge["node"]
                items.append({
                    "raw_title": node["name"],
                    "raw_text": f"{node['tagline']}. {node.get('description','')}"[:1200],
                    "url": node["url"],
                    "source": "Product Hunt",
                    "likes": node.get("votesCount"),
                    "comments": node.get("commentsCount"),
                    "shares": None,
                })
        except Exception as e:
            print(f"[warn] Product Hunt fetch failed for topic {topic}: {e}")
    return items


# ---- Step 2: classify + score via Claude -------------------------------

SCORING_PROMPT = """You are triaging items for a tracker that feeds an article-writing pipeline
covering innovation in Music, Fintech, and AI Marketing & Growth.

Given the raw item below, respond with ONLY a JSON object (no prose, no markdown fences):
{{
  "is_relevant": true/false,   // false if this doesn't fit any of the 3 verticals or isn't about a real product/idea
  "vertical": one of {verticals},
  "category": one of {categories},
  "name": short product/idea name,
  "description": one-sentence plain description,
  "innovation": one-sentence explanation of what's actually new or valuable here (be skeptical of hype; if it's not genuinely novel, say so plainly),
  "relevance_score": 0-100,      // fit to the 3 verticals + how article-worthy the topic is
  "novelty_score": 0-100,        // genuine innovation vs. repackaging of existing ideas
  "applicability_score": 0-100   // relevance to a technical PM building consumer apps (guitar learning app, budgeting app)
}}

Raw item:
Title: {title}
Text: {text}
"""

def classify_and_score(raw_item):
    prompt = SCORING_PROMPT.format(
        verticals=VERTICALS, categories=CATEGORIES,
        title=raw_item["raw_title"], text=raw_item["raw_text"],
    )
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip()
    text = re.sub(r"^```json|```$", "", text.strip()).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        print(f"[warn] Could not parse model output for '{raw_item['raw_title']}'")
        return None
    if not parsed.get("is_relevant"):
        return None
    return parsed


def engagement_score(likes, comments, shares):
    """Normalize engagement to 0-100. RSS items with no data get a neutral default."""
    if likes is None and comments is None and shares is None:
        return 40  # neutral score when no engagement data exists (e.g. RSS-only items)
    total = (likes or 0) + (comments or 0) * 2 + (shares or 0) * 1.5
    return min(100, round(total / 8))  # rough normalization, tune against real data


def weighted_total(scores):
    return round(sum(scores[k] * WEIGHTS[k] for k in WEIGHTS), 1)


# ---- Main ---------------------------------------------------------------

def main():
    raw_items = fetch_rss_items() + fetch_product_hunt_items()
    print(f"Fetched {len(raw_items)} raw candidates.")

    results = []
    for raw in raw_items[:MAX_ITEMS_TO_SCORE]:
        parsed = classify_and_score(raw)
        if not parsed:
            continue
        eng_score = engagement_score(raw["likes"], raw["comments"], raw["shares"])
        scores = {
            "relevance": parsed["relevance_score"],
            "engagement": eng_score,
            "novelty": parsed["novelty_score"],
            "applicability": parsed["applicability_score"],
        }
        total = weighted_total(scores)
        results.append({
            "vertical": parsed["vertical"],
            "category": parsed["category"],
            "name": parsed["name"],
            "description": parsed["description"],
            "innovation": parsed["innovation"],
            "source": raw["source"],
            "url": raw["url"],
            "engagement": {
                "likes": raw["likes"] or 0,
                "comments": raw["comments"] or 0,
                "shares": raw["shares"] or 0,
            },
            "score_breakdown": scores,
            "score": total,
            "article_worthy": total >= ARTICLE_WORTHY_THRESHOLD,
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    with open("data.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"Scored {len(results)} relevant items.")
    print(f"Article-worthy: {sum(1 for r in results if r['article_worthy'])}")
    print(f"Run completed at {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
