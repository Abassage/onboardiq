#!/usr/bin/env python3
"""OnboardIQ - HR onboarding Q&A agent.

Retrieves relevant sections from a sample employee handbook and answers
new-hire questions with an LLM, grounded ONLY in the retrieved excerpts.
Sensitive topics and low-confidence questions escalate to HR instead of
being answered - the human-in-the-loop control.

Built as a demo for a People AI & Automation Engineer application.
Run:  OPENAI_API_KEY=sk-... python onboardiq.py
Test without an API key:  python onboardiq.py --dry-run
"""
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- load & chunk
def load_chunks(path):
    """Split the handbook into one chunk per ## section."""
    text = open(path, encoding="utf-8").read()
    parts = re.split(r"(?m)^## ", text)
    chunks = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        title, _, body = part.partition("\n")
        chunks.append((title.strip(), body.strip()))
    return chunks

# --------------------------------------------------------------- retrieve
STOPWORDS = set(
    "a an the and or of to in on for with is are was were be been do does "
    "did what when where who how many much can i my me we you your our it its "
    "this that those these as at by from get work".split()
)

def stem(word):
    """Light stemming so related forms match (expenses/expense, remotely/remote)."""
    if len(word) > 5 and word.endswith("ies"):
        return word[:-3] + "y"
    for suffix in ("ing", "edly", "ed", "ly"):
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            return word[: -len(suffix)]
    if len(word) > 3 and word.endswith("s"):
        return word[:-1]
    return word

def tokens(text):
    return [stem(t) for t in re.findall(r"[a-z0-9]+", text.lower())
            if t not in STOPWORDS]

def retrieve(question, chunks, k=3):
    """Score chunks by keyword overlap with the question; title matches count double."""
    q = set(tokens(question))
    scored = []
    for title, body in chunks:
        overlap = len(q & set(tokens(title + " " + body)))
        title_overlap = len(q & set(tokens(title)))
        scored.append((overlap + 2 * title_overlap, title, body))
    scored.sort(key=lambda s: s[0], reverse=True)
    return [(score, title, body) for score, title, body in scored[:k] if score > 0]

# Minimum retrieval score to answer; below this we escalate for no coverage.
MIN_SCORE = 2

# --------------------------------------------------------------- escalate
SENSITIVE = [
    "salary", "pay raise", "compensation", "bonus",
    "lawsuit", "sue", "legal", "lawyer",
    "disability", "accommodation", "medical",
    "fired", "firing", "termination", "layoff",
    "harassment", "discrimination",
]

def escalation_reason(question, hits):
    """Return a reason to escalate to HR, or None if safe to answer."""
    q = question.lower()
    if any(word in q for word in SENSITIVE):
        return "sensitive topic"
    if not hits or hits[0][0] < MIN_SCORE:
        return "no handbook coverage"
    return None

# --------------------------------------------------------------- answer
SYSTEM_PROMPT = (
    "You are OnboardIQ, an HR onboarding assistant. Answer ONLY from the "
    "handbook excerpts provided below. Keep answers to 2-3 sentences. If the "
    "excerpts do not cover the question, say so and direct the employee to HR."
)

def build_messages(question, hits):
    context = "\n\n".join(f"[{title}]\n{body}" for _, title, body in hits)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",
         "content": f"Handbook excerpts:\n{context}\n\nQuestion: {question}"},
    ]

def answer(question, hits):
    from openai import OpenAI  # imported here so --dry-run needs no API key
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=build_messages(question, hits),
        temperature=0.2,
    )
    return response.choices[0].message.content

# --------------------------------------------------------------- cli
def main():
    dry_run = "--dry-run" in sys.argv
    chunks = load_chunks(os.path.join(BASE, "handbook", "handbook.md"))
    print("OnboardIQ ready. Ask onboarding questions ('quit' to exit).")
    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if question.lower() in ("quit", "exit"):
            break
        if not question:
            continue
        hits = retrieve(question, chunks)
        reason = escalation_reason(question, hits)
        if reason:
            print(f"OnboardIQ: That looks like a {reason} question - "
                  f"I'm looping in HR rather than guessing.")
            continue
        if dry_run:
            messages = build_messages(question, hits)
            print("OnboardIQ [dry-run - retrieved sections: "
                  + ", ".join(t for _, t, _ in hits) + "]")
            print("Prompt preview:", messages[1]["content"][:400], "...")
        else:
            print("OnboardIQ:", answer(question, hits))

if __name__ == "__main__":
    main()
