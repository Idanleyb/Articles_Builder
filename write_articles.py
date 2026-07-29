"""
Article Writer — runs Mondays and Wednesdays.

WHAT THIS DOES
1. Reads the latest data.json (from fetch_and_score.py) and selected_for_writing.json.
2. Picks the item(s) to write about:
   - If selected_for_writing.json has names in it, use those (manual pick wins).
   - Otherwise, fall back to the single highest-scoring item not already in written_log.json.
3. Generates each article using the article-writer skill's rules (tone guide,
   LinkedIn formatting, SEO/GEO) via the Claude API.
4. Appends each finished article to a Google Doc.
5. Records what was written in written_log.json (so it's never reused) and
   clears selected_for_writing.json.

REQUIRED ENV VARS (GitHub Actions secrets):
  ANTHROPIC_API_KEY            - already set up for fetch_and_score.py
  GOOGLE_SERVICE_ACCOUNT_JSON  - full contents of the service account key file
  GOOGLE_DOC_ID                - the ID of the Google Doc to append articles to
                                 (the long string in the doc's URL between /d/ and /edit)

RUN LOCALLY:
  pip install -r requirements.txt
  export ANTHROPIC_API_KEY=...
  export GOOGLE_SERVICE_ACCOUNT_JSON="$(cat service-account-key.json)"
  export GOOGLE_DOC_ID=...
  python write_articles.py
"""
import json
import os
from datetime import datetime, timezone

from anthropic import Anthropic
from google.oauth2 import service_account
from googleapiclient.discovery import build

DATA_FILE = "data.json"
SELECTED_FILE = "selected_for_writing.json"
WRITTEN_LOG_FILE = "written_log.json"

TONE_GUIDE = """
CORE VOICE & IDENTITY PILLARS
1. The Technical Marketer — view every topic through a product/technique lens:
   mechanics, funnels, user behavior, strategic frameworks. Sell ideas by making
   the substance so compelling the value is self-evident.
2. The Musician's Mindset — infuse rhythm, harmony, and storytelling. Draw
   parallels between composition, improvisation, practice, and market dynamics
   whenever authentic (never forced).
3. Easy-Going & Professional — confident, conversational. No stiff corporate
   jargon. Respect the reader's intelligence and time.
4. Classy Humor — witty, subtle, self-aware. Never cheap gags or forced memes.
   Should feel like a clever aside over coffee.

NON-NEGOTIABLE RULES
- Every article must leave a concrete takeaway or new mental model. Never filler.
- Zero cheesy hype language ("game-changer," "skyrocket," "revolutionary secret").
- No generic intros ("In today's fast-paced digital world..."). Start inside the context.
- Rhythmic cadence: alternate short punchy statements with longer descriptive ones.

STRUCTURE
1. The Hook — an observation, real scene, or sharp technical question.
2. The Mechanics/Story — unpack the underlying technique or creative analogy. Show, don't tell.
3. The Core Observation — the "Aha!" moment or practical principle.
4. The Takeaway — a clean summary of what to do next; the value sells itself.

CONTRAST EXAMPLES (avoid -> use instead)
- "Want to skyrocket your conversion rate? 5 growth hacks you must know today!"
  -> "Conversion optimization isn't about tricks; it's about tension and resolution.
      Like resolving a minor chord, every click should feel like the natural next step."
- "In this fast-paced world, staying ahead of the curve is more critical than ever."
  -> "Execution speed matters, but tempo matters more. Rush the timing on a product
      feature, and even the best campaign sounds out of key."
"""

ARTICLE_PROMPT = """Write a LinkedIn article based on the source item below, following
the tone guide and requirements exactly.

TONE GUIDE:
{tone_guide}

REQUIREMENTS:
- Fit LinkedIn conventions: natural short paragraphs, no markdown syntax (no **bold**,
  no # headers) since LinkedIn won't render it, 3-5 relevant hashtags at the end.
- Apply SEO: work the core topic naturally into the first 2 sentences.
- Apply GEO: state the core claims clearly and directly somewhere in the piece,
  so an AI assistant summarizing this topic later could accurately cite it,
  even while keeping the voice/metaphor elsewhere.
- Length: 350-550 words.
- Follow the structural blueprint: Hook -> Mechanics/Story -> Core Observation -> Takeaway.

SOURCE ITEM:
Name: {name}
Vertical: {vertical}
Category: {category}
Description: {description}
Innovation: {innovation}

Respond with ONLY a JSON object (no prose, no markdown fences):
{{
  "title": "...",
  "body": "...",
  "hashtags": ["...", "..."]
}}
"""

client = Anthropic()


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def pick_items(data, selected, written_log):
    written_names = {w["name"] for w in written_log}
    selected_names = selected.get("selected_names", [])

    if selected_names:
        items = [d for d in data if d["name"] in selected_names]
        missing = set(selected_names) - {i["name"] for i in items}
        if missing:
            print(f"[warn] Selected names not found in latest data.json: {missing}")
        return items

    # Fallback: highest-scoring item not yet written about. Not gated on the
    # article_worthy flag (75+) — that flag is a dashboard quality signal, but
    # the writer should still produce something on days without a standout item.
    candidates = [d for d in data if d["name"] not in written_names]
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:1]


def generate_article(item):
    prompt = ARTICLE_PROMPT.format(
        tone_guide=TONE_GUIDE,
        name=item["name"], vertical=item["vertical"], category=item["category"],
        description=item["description"], innovation=item["innovation"],
    )
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip()
    text = text.removeprefix("```json").removesuffix("```").strip()
    return json.loads(text)


def append_to_google_doc(doc_id, entries):
    """entries: list of dicts with title, body, hashtags, source_name, source_vertical."""
    creds_json = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    creds = service_account.Credentials.from_service_account_info(
        creds_json, scopes=["https://www.googleapis.com/auth/documents"]
    )
    service = build("docs", "v1", credentials=creds)

    # Find current end of doc so we append rather than overwrite.
    doc = service.documents().get(documentId=doc_id).execute()
    end_index = doc["body"]["content"][-1]["endIndex"] - 1

    requests = []
    for entry in entries:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        block = (
            f"\n\n---\n{date_str} | {entry['source_vertical']} | source: {entry['source_name']}\n"
            f"{entry['title']}\n\n"
            f"{entry['body']}\n\n"
            f"{' '.join('#' + h.lstrip('#') for h in entry['hashtags'])}\n"
        )
        requests.append({
            "insertText": {"location": {"index": end_index}, "text": block}
        })
        end_index += len(block)

    service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()


def main():
    data = load_json(DATA_FILE, [])
    if not data:
        print("[error] data.json is empty or missing — run fetch_and_score.py first.")
        return

    selected = load_json(SELECTED_FILE, {"selected_names": []})
    written_log = load_json(WRITTEN_LOG_FILE, [])

    items = pick_items(data, selected, written_log)
    if not items:
        print("[info] Nothing to write about — no manual selection and no unwritten article-worthy items.")
        return

    doc_id = os.environ.get("GOOGLE_DOC_ID")
    entries = []
    for item in items:
        print(f"Writing article for: {item['name']} ({item['vertical']})")
        article = generate_article(item)
        entries.append({
            "title": article["title"],
            "body": article["body"],
            "hashtags": article["hashtags"],
            "source_name": item["name"],
            "source_vertical": item["vertical"],
        })
        written_log.append({
            "name": item["name"],
            "written_at": datetime.now(timezone.utc).isoformat(),
            "title": article["title"],
        })

    if doc_id:
        append_to_google_doc(doc_id, entries)
        print(f"Appended {len(entries)} article(s) to Google Doc {doc_id}")
    else:
        print("[warn] GOOGLE_DOC_ID not set — skipping Google Docs push. Articles generated but not saved externally:")
        for e in entries:
            print(json.dumps(e, indent=2))

    save_json(WRITTEN_LOG_FILE, written_log)
    save_json(SELECTED_FILE, {"_instructions": selected.get("_instructions", ""), "selected_names": []})
    print("Cleared selected_for_writing.json and updated written_log.json")


if __name__ == "__main__":
    main()
