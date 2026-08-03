"""
Sample data generator for the Music / Fintech / AI-Marketing-Growth tracker.

This stands in for the real daily pipeline until API keys are wired in.
Once live, `fetch_and_score.py` replaces this file's role: it will pull
real items from RSS feeds + Product Hunt, score them with the same
weighting logic, and write to data.json in the same shape.
"""
import json
import random
from datetime import datetime, timezone, timedelta

random.seed(7)

WEIGHTS = {
    "relevance": 0.40,
    "engagement": 0.30,
    "novelty": 0.20,
    "applicability": 0.10,
}

ARTICLE_WORTHY_THRESHOLD = 75

RAW_ITEMS = [
    # ---- AI Marketing / Growth ----
    {
        "vertical": "AI Marketing & Growth",
        "category": "Content AI",
        "name": "Adaptive Ad-Copy Generator",
        "description": "A tool that rewrites ad copy per-audience-segment in real time, using response data instead of static A/B tests.",
        "innovation": "Collapses A/B testing cycles from weeks to hours by treating copy as a continuously-optimized variable rather than a fixed asset.",
        "source": "Marketing AI Institute",
        "likes": 412, "comments": 58, "shares": 91,
        "scores": {"relevance": 95, "engagement": 78, "novelty": 70, "applicability": 60},
    },
    {
        "vertical": "AI Marketing & Growth",
        "category": "Analytics & Insights",
        "name": "Attribution-Free Funnel Mapper",
        "description": "Uses probabilistic modeling instead of pixel-based tracking to estimate channel contribution as cookies disappear.",
        "innovation": "Sidesteps the privacy/tracking collapse entirely rather than patching around it.",
        "source": "Exploding Topics",
        "likes": 289, "comments": 34, "shares": 47,
        "scores": {"relevance": 90, "engagement": 60, "novelty": 82, "applicability": 55},
    },
    {
        "vertical": "AI Marketing & Growth",
        "category": "Automation & Workflow",
        "name": "Agent-Run Growth Experiments",
        "description": "An autonomous agent that proposes, launches, and kills growth experiments on landing pages without a human approving each step.",
        "innovation": "Moves growth teams from 'agent suggests, human decides' to 'agent decides, human audits' — a genuine workflow shift.",
        "source": "Ben's Bites",
        "likes": 601, "comments": 112, "shares": 140,
        "scores": {"relevance": 88, "engagement": 92, "novelty": 88, "applicability": 50},
    },
    {
        "vertical": "AI Marketing & Growth",
        "category": "Other / Emerging",
        "name": "Synthetic Focus Groups",
        "description": "Simulates customer panels using persona-tuned LLMs to pre-test messaging before a real campaign spend.",
        "innovation": "Cuts research cost, but the real innovation is treating simulated feedback as a rough filter, not a replacement for real users.",
        "source": "Superhuman AI",
        "likes": 175, "comments": 22, "shares": 19,
        "scores": {"relevance": 80, "engagement": 40, "novelty": 55, "applicability": 45},
    },
    {
        "vertical": "AI Marketing & Growth",
        "category": "Content AI",
        "name": "GEO-Native Content Briefs",
        "description": "Generates content briefs optimized for how generative engines (not just search engines) cite and summarize brands.",
        "innovation": "One of the first tools built for 'generative engine optimization' as a discipline distinct from SEO.",
        "source": "Marketing AI Institute",
        "likes": 520, "comments": 88, "shares": 133,
        "scores": {"relevance": 98, "engagement": 85, "novelty": 90, "applicability": 75},
    },

    # ---- Fintech ----
    {
        "vertical": "Fintech",
        "category": "Analytics & Insights",
        "name": "Cash-Flow Forecast Copilot",
        "description": "Reads a small business's transaction history and forecasts cash-flow gaps 30-60 days out with plain-language explanations.",
        "innovation": "Explains *why* a gap is predicted, not just that one exists — closes the trust gap that kills adoption of forecasting tools.",
        "source": "Product Hunt",
        "likes": 340, "comments": 41, "shares": 30,
        "scores": {"relevance": 85, "engagement": 65, "novelty": 65, "applicability": 80},
    },
    {
        "vertical": "Fintech",
        "category": "Automation & Workflow",
        "name": "Auto-Categorizing Ledger Agent",
        "description": "An agent that categorizes bank/card transactions and flags anomalies, learning per-user categorization habits instead of using fixed rules.",
        "innovation": "Personalized categorization logic per household/business rather than a shared static rule set.",
        "source": "Product Hunt",
        "likes": 298, "comments": 37, "shares": 22,
        "scores": {"relevance": 82, "engagement": 55, "novelty": 58, "applicability": 92},
    },
    {
        "vertical": "Fintech",
        "category": "Other / Emerging",
        "name": "Conversational Underwriting Assistant",
        "description": "Lets loan officers query underwriting models in natural language instead of navigating rule engines.",
        "innovation": "Makes black-box credit models auditable in plain conversation — a real transparency step, not just a UI skin.",
        "source": "Fintech Brainfood",
        "likes": 210, "comments": 29, "shares": 18,
        "scores": {"relevance": 75, "engagement": 45, "novelty": 72, "applicability": 40},
    },
    {
        "vertical": "Fintech",
        "category": "Content AI",
        "name": "Plain-Language Statement Generator",
        "description": "Rewrites dense financial statements and disclosures into plain language tailored to a reader's financial literacy level.",
        "innovation": "Targets financial literacy directly as a product feature rather than a compliance afterthought.",
        "source": "Fintech Brainfood",
        "likes": 156, "comments": 15, "shares": 12,
        "scores": {"relevance": 70, "engagement": 30, "novelty": 60, "applicability": 65},
    },
    {
        "vertical": "Fintech",
        "category": "Analytics & Insights",
        "name": "Merchant Risk Signal Aggregator",
        "description": "Combines transaction velocity, review sentiment, and public filings into a single fraud/risk score updated daily.",
        "innovation": "Fuses previously siloed signal types (behavioral + reputational + regulatory) into one continuously-updating score.",
        "source": "Product Hunt",
        "likes": 380, "comments": 52, "shares": 44,
        "scores": {"relevance": 88, "engagement": 70, "novelty": 68, "applicability": 55},
    },

    # ---- Music ----
    {
        "vertical": "Music",
        "category": "Content AI",
        "name": "Stem-Aware Practice Coach",
        "description": "Isolates instrument stems from any reference track in real time and adapts practice exercises to what the player is struggling with.",
        "innovation": "Turns any commercial recording into a personalized lesson plan on the fly, rather than relying on pre-made tutorials.",
        "source": "Music Ally",
        "likes": 265, "comments": 33, "shares": 40,
        "scores": {"relevance": 92, "engagement": 62, "novelty": 75, "applicability": 90},
    },
    {
        "vertical": "Music",
        "category": "Analytics & Insights",
        "name": "Fan-Intent Forecasting",
        "description": "Predicts which fans are close to converting from streaming to ticket/merch purchases, based on listening-pattern shifts.",
        "innovation": "Uses listening behavior as a leading indicator of purchase intent, not just a lagging engagement metric.",
        "source": "Music Business Worldwide",
        "likes": 198, "comments": 20, "shares": 15,
        "scores": {"relevance": 78, "engagement": 42, "novelty": 66, "applicability": 50},
    },
    {
        "vertical": "Music",
        "category": "Automation & Workflow",
        "name": "Auto-Generated Practice Curricula",
        "description": "Builds a week-by-week curriculum for a learner based on skill assessments, adjusting difficulty automatically as they progress.",
        "innovation": "Replaces static method books with a curriculum that re-plans itself after every session.",
        "source": "Music Ally",
        "likes": 445, "comments": 67, "shares": 80,
        "scores": {"relevance": 95, "engagement": 80, "novelty": 78, "applicability": 95},
    },
    {
        "vertical": "Music",
        "category": "Other / Emerging",
        "name": "AI Co-Writer for Song Structure",
        "description": "Suggests structural alternatives (bridge placement, section length) for a work-in-progress song without generating the actual lyrics or melody.",
        "innovation": "Keeps the human as sole author of creative content while assisting with structural craft — a narrower, less controversial use of generative AI in music.",
        "source": "Music Business Worldwide",
        "likes": 310, "comments": 48, "shares": 35,
        "scores": {"relevance": 80, "engagement": 58, "novelty": 70, "applicability": 45},
    },
    {
        "vertical": "Music",
        "category": "Content AI",
        "name": "Setlist Personalization Engine",
        "description": "Suggests live setlists per venue/city based on local streaming data, so touring acts can tailor shows to regional fan behavior.",
        "innovation": "Applies growth-marketing-style segmentation logic to something as traditionally 'gut-feel' as a live setlist.",
        "source": "Music Ally",
        "likes": 227, "comments": 25, "shares": 21,
        "scores": {"relevance": 84, "engagement": 48, "novelty": 74, "applicability": 55},
    },
]


def weighted_score(scores):
    return round(sum(scores[k] * WEIGHTS[k] for k in WEIGHTS), 1)


def build():
    items = []
    now = datetime.now(timezone.utc)
    for i, raw in enumerate(RAW_ITEMS):
        total = weighted_score(raw["scores"])
        # Stagger sample timestamps across the last few days so date sorting
        # has something meaningful to demonstrate.
        published_at = (now - timedelta(days=i % 4, hours=i)).isoformat()
        item = {
            "vertical": raw["vertical"],
            "category": raw["category"],
            "name": raw["name"],
            "description": raw["description"],
            "innovation": raw["innovation"],
            "source": raw["source"],
            "published_at": published_at,
            "engagement": {
                "likes": raw["likes"],
                "comments": raw["comments"],
                "shares": raw["shares"],
            },
            "score_breakdown": raw["scores"],
            "score": total,
            "article_worthy": total >= ARTICLE_WORTHY_THRESHOLD,
        }
        items.append(item)
    items.sort(key=lambda x: x["score"], reverse=True)
    return items


if __name__ == "__main__":
    data = build()
    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {len(data)} items to data.json")
    print(f"Article-worthy (score >= {ARTICLE_WORTHY_THRESHOLD}): "
          f"{sum(1 for d in data if d['article_worthy'])}")
