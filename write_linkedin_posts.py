"""
LinkedIn Post Writer — runs Tuesdays and Thursdays (2 posts/week total, one
per run day). Rotates through 5 fixed topics and emails each finished post —
this is separate from write_articles.py (long-form articles, Google Doc,
Mon/Wed), using the shorter-form linkedin-post-writer skill instead.

REQUIRED ENV VARS (GitHub Actions secrets):
  ANTHROPIC_API_KEY   - already set up
  GMAIL_ADDRESS        - the Gmail account to send from AND to (sending to yourself)
  GMAIL_APP_PASSWORD   - a Gmail App Password (NOT your regular password —
                          Gmail requires this for SMTP with 2FA enabled)

RUN LOCALLY:
  pip install anthropic
  export ANTHROPIC_API_KEY=...
  export GMAIL_ADDRESS=you@gmail.com
  export GMAIL_APP_PASSWORD=...
  python write_linkedin_posts.py
"""
import json
import os
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText

from anthropic import Anthropic

LOG_FILE = "linkedin_post_log.json"

TOPICS = ["Marketing", "Psychological Marketing", "Fintech", "Music", "AI"]

TONE_GUIDE = """
CORE IDENTITY & VOICE PILLARS
1. Authentically Human (Non-Native Polish) — write like you speak over coffee.
   Warm, sincere phrasing ("cherish with me so much memories," "one of a kind,"
   "not a walk in the park"). Don't over-correct grammar into sterile corporate
   English — the personal, direct touch is what builds connection.
2. Routine & Real Life Anchors — start on a real, unglamorous daily moment
   (wrestling with campaign data at 8 AM, cold coffee, a late-night Zoom call,
   fixing a guitar chord before a product review). Concrete moments make
   technical insights relatable.
3. Classy, Self-Aware Humor — laugh gently at the chaos of tech, building
   products, and corporate life. Short, self-deprecating side notes or dry
   observations. Never forced.
4. Technical Marketer + Musician's Mindset — view topics through product
   mechanics, user funnels, and real market data, but frame with a musician's
   sense of tempo, harmony, and composition.

NON-NEGOTIABLE RULES
- Short paragraphs & breathing room — frequent line breaks, easy to read on mobile.
- No empty corporate fluff ("In today's fast-paced digital ecosystem..."). Jump
  straight into the story, data point, or observation.
- Always have a takeaway — an observation, a lesson, or an interesting link.

FRAMEWORKS (pick whichever fits the topic — don't force one every time)
- Framework 1, Daily Routine + Lesson (default for most posts): open on a real
  unglamorous moment, draw a genuine parallel to music/craft practice, land on
  a product/marketing principle, close with a question inviting the reader's
  own story.
- Framework 2, Industry Insight/Data Point: open with a specific real stat or
  finding, explain what it actually signals about where the space is moving.
- Framework 3, Career Milestone/Personal Journey: only for genuine personal
  news — not a default. Short emotional beat, warm reflection, close with
  forward momentum, not a mic-drop.

PRE-POST CHECKLIST
- Does it sound like talking over coffee? (Warm, direct, slightly informal)
- Is there a touch of humor or self-irony?
- Is it anchored in a real example, data point, or daily event?
- Is the formatting easy to read on a phone?
"""

POST_PROMPT = """Write a short LinkedIn POST (not a long-form article) on this topic: {topic}.

"Psychological Marketing" (if this is the topic) means the psychology behind
marketing and consumer decisions — cognitive biases, persuasion mechanics,
decision framing — not generic marketing advice.

TONE GUIDE:
{tone_guide}

FORMAT RULES:
- Length: 50-150 words. This is a POST, not an article — one idea, tightly delivered.
- Pick whichever of the 3 frameworks in the tone guide actually fits this
  topic (don't default to the same one every time) — Framework 3 (career
  milestone) only applies to genuine personal news, so for topic-driven posts
  use Framework 1 or 2.
- Short lines, generous whitespace — read on a phone, scrolling fast.
- No markdown syntax (no **bold**, no # headers).
- 3-5 relevant hashtags at the end.
- An optional closing question/provocation is fine ONLY if genuinely earned by
  the point — never a generic "What do you think?" tack-on.

Respond with ONLY a JSON object (no prose, no markdown fences):
{{
  "body": "...",
  "hashtags": ["...", "..."],
  "framework_used": "1, 2, or 3"
}}
"""

client = Anthropic()


def load_log():
    if not os.path.exists(LOG_FILE):
        return {"total_sent": 0, "history": []}
    with open(LOG_FILE) as f:
        return json.load(f)


def save_log(log):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


def generate_post(topic):
    prompt = POST_PROMPT.format(topic=topic, tone_guide=TONE_GUIDE)
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip()
    text = text.removeprefix("```json").removesuffix("```").strip()
    return json.loads(text)


def send_email(post_number, topic, date_str, body, hashtags, framework_used):
    gmail_address = os.environ["GMAIL_ADDRESS"]
    gmail_app_password = os.environ["GMAIL_APP_PASSWORD"]

    hashtag_line = " ".join("#" + h.lstrip("#") for h in hashtags)
    subject = f"LinkedIn Post #{post_number} — {topic} — {date_str}"
    full_body = (
        f"Date: {date_str}\n"
        f"LinkedIn post number: {post_number}\n"
        f"Topic: {topic}\n"
        f"Framework used: {framework_used}\n"
        f"{'-' * 40}\n\n"
        f"{body}\n\n{hashtag_line}"
    )

    msg = MIMEText(full_body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = gmail_address
    msg["To"] = gmail_address

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, gmail_app_password)
        server.sendmail(gmail_address, [gmail_address], msg.as_string())


def main():
    log = load_log()
    topic = TOPICS[log["total_sent"] % len(TOPICS)]
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print(f"Generating LinkedIn post #{log['total_sent'] + 1} on topic: {topic}")
    post = generate_post(topic)

    post_number = log["total_sent"] + 1
    framework_used = post.get("framework_used", "unspecified")
    send_email(post_number, topic, date_str, post["body"], post["hashtags"], framework_used)
    print(f"Emailed post #{post_number} ({topic}, framework {framework_used}) to {os.environ['GMAIL_ADDRESS']}")

    log["total_sent"] = post_number
    log["history"].append({
        "post_number": post_number,
        "topic": topic,
        "date": date_str,
        "framework_used": framework_used,
        "body_preview": post["body"][:120],
    })
    save_log(log)


if __name__ == "__main__":
    main()
