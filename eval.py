"""Evaluate retrieval on a hand-labelled question set.

Each question lists the chunk IDs that answer it (labelled by hand,
independently of the retriever) and whether the guide covers it.
run_eval checks whether retrieve() finds an expected chunk in its top 3,
and whether off-topic questions are rejected by the score threshold.
"""

import json
from pathlib import Path
import re
import sys
from retriever import retrieve
import time

DATA_DIR = Path("data/software_engineering")
DEBUG_DIR = Path("debug")
DEBUG = "--debug" in sys.argv

with open(DATA_DIR / "chunks.json",encoding="utf-8") as f:
    chunks = json.load(f)

EVAL_SET = [
    {"question": "What is Unit Testing", "answerable": True,
     "expected": ["ch05-2.1.1.", "ch04-5.3."]},
    {"question": "What is Software Engineering", "answerable": True,
     "expected": ["intro-p2", "intro-p3"]},
    {"question": "What is System Design", "answerable": True,
     "expected": ["ch03-intro-p1", "ch16-1.-p2", "ch16-2.2.5.-p1"]},
    {"question": "What are the different Architectural Patterns?", "answerable": True,
     "expected": ["ch02-2.2.-p1", "ch02-2.2.-p2", "ch03-4.4."]},
    {"question": "Types of software testings?", "answerable": True,
     "expected": ["ch05-2."]},
    {"question": "What is SDLC? Types of life cycles.", "answerable": True,
     "expected": ["ch10-2.1.-p1", "ch10-2.4.-p1", "ch10-2.5.-p1"]},
    {"question": "How machine learning applied in software development", "answerable": True,
     "expected": ["ch16-9.6.-p1", "ch16-9.6.-p2", "ch13-6.3."]},
    {"question": "Give me one architectural structure", "answerable": True,
     "expected": ["ch02-2.1.-p1", "ch02-3.2.-p1", "ch02-3.2.-p2"]},
    {"question": "What is cyber security?", "answerable": True,
     "expected": ["ch13-intro", "ch13-1.", "ch13-1.3."]},
    {"question": "How we secure the software applications?", "answerable": True,
     "expected": ["ch13-1.", "ch13-3.1."]},
    {"question": "What is requirements elicitation?", "answerable": True,
     "expected": ["ch01-2.", "ch01-2.2.-p1"]},
    {"question": "What is refactoring?", "answerable": True,
     "expected": ["ch07-4.2.", "ch11-4.4.-p1"]},
    {"question": "What are the types of software maintenance?", "answerable": True,
     "expected": ["ch07-1.6.-p1", "ch07-1.6.-p2"]},
    {"question": "What is a configuration baseline?", "answerable": True,
     "expected": ["ch08-2.1.1.-p2"]},
    {"question": "What is the purpose of a code review?", "answerable": True,
     "expected": ["ch12-3.4.5.-p1", "ch09-4."]},
    {"question": "What is technical debt?", "answerable": True,
     "expected": ["ch07-2.3.1.-p1", "ch07-2.3.1.-p2"]},
    {"question": "What are a software engineer's ethical responsibilities?", "answerable": True,
     "expected": ["ch14-1.2.", "ch12-1.1."]},

    # Off-topic: should be rejected
    {"question": "How to make a Bread?", "answerable": False, "expected": []},
    {"question": "Who won the 2023 Cricket World Cup?", "answerable": False, "expected": []},
    {"question": "What is the capital of France?", "answerable": False, "expected": []},
    {"question": "How do I configure a Kubernetes ingress?", "answerable": False, "expected": []},
    {"question": "What is the latest version of Python?", "answerable": False, "expected": []},
]

STOP_WORDS = {
    "what", "is", "are", "how", "do", "does", "we", "i", "the", "a", "an",
    "of", "in", "to", "for", "and", "or", "me", "give", "one", "types",
    "different", "explain", "can", "you", "why", "which",
}

MIN_KEYWORD_SCORE = 3 

def extract_keyword(question):
    """Return the meaningful words of a question.

    Lowercases the question, keeps only letters, and drops common
    words in STOP_WORDS (e.g. "what", "is", "the")."""

    keywords = []
    words = re.findall(r"[a-z]+", question.lower())
    for word in words:
        if word not in STOP_WORDS:
            keywords.append(word)
    return keywords

def find(question,top=10):
    """Suggest candidate chunks for labelling, using keyword overlap.

    Scores each chunk as 3 x (keywords in the heading) + (keywords in the text),
    keeps chunks at or above a minimum that scales with the number of keywords,
    and returns the top results as (score, id, heading), highest first.
    A labelling helper only: it is not used by run_eval."""

    kw = set(extract_keyword(question))
    min_score = 1 if len(kw) <= 2 else MIN_KEYWORD_SCORE
    scored = []
    for c in chunks:
        heading_words = set(re.findall(r"[a-z]+", c["heading"].lower()))
        text_words = set(re.findall(r"[a-z]+", c["text"].lower()))
        score = 3 * len(kw& heading_words) +  len(kw & text_words)
        if score >= min_score:
            scored.append((score, c["id"], c["heading"]))

        
    scored.sort(reverse=True)
    return scored[:top]

def run_eval(testcases):
    """Count retrieval hits for answerable questions and rejections for off-topic ones.

    An answerable question is a hit if any of its expected IDs appears in
    retrieve()'s top 3. An off-topic question is correctly rejected if no
    chunk passes MIN_SCORE. Pauses 60 seconds after every 3 questions for
    Voyage's free tier, then prints both scores and every miss."""

    hits, answerable, fallback_ok, off_topic = 0,0,0,0
    misses = []
   
    for n, case in enumerate(testcases, start=1):
        ids = [c["id"] for c in retrieve(case["question"])]

        if case["answerable"]:
            answerable += 1
            if any(e in ids for e in case["expected"]):
                hits += 1
            else:
                misses.append((case["question"], ids))
        else:
            off_topic += 1
            if not ids:                           # nothing above MIN_SCORE → fallback
                fallback_ok += 1
            else:
                misses.append((case["question"], ids))

        if n % 3 == 0:                               # Voyage free tier: 3 requests a minute
            time.sleep(60)

    print(f"Retrieval: {hits}/{answerable} hits @3")
    print(f"Off-topic: {fallback_ok}/{off_topic} correctly rejected")
    for q, ids in misses:
        print("MISS:", q, ids)

if __name__ == "__main__":
    if DEBUG:
        for o in EVAL_SET:
            print(find(o["question"]))
            with open(DATA_DIR / "evals.json", "w", encoding="utf-8") as f:
                json.dump(find(o["question"]),f,ensure_ascii=False)

    run_eval(EVAL_SET)