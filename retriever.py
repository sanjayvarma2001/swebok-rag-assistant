""" 1. What this file do?
    2. What input does it take?
    3. What will be the output?
    4. How it works on it?
     - Retrieve the chunks most relevant to a user's question.

     - Input: the question (a string) and the embedded chunks from embeddings.json.
     - Output: the top-k chunks (id, heading, text, score), most similar first.

     - How it works:
        1. Embeds the prompt with voyage(input_type="query")
        2. Compute cosine similarity between the question vector and every chunk vector.
        3. Sort by score and return the top k (default 3).
    
    llm.py then puts these chunks and the question into the prompt for Gemini.
"""
from voyageai.error import RateLimitError
from config import EMBED_MODEL, voyage_client
from pathlib import Path
import json
import math


DATA_DIR = Path("data/software_engineering")

with open(DATA_DIR / "embeddings.json", encoding="utf-8") as f:
    embeddings = json.load(f)

def embed_prompt(query):
    """Embed a question with Voyage (input_type="query").

    Returns one vector of 1024 numbers."""

    try:
        embedding = voyage_client.embed([query], model=EMBED_MODEL, input_type="query")
        return embedding.embeddings[0]
    except RateLimitError:
        raise RuntimeError("Voyage rate limit reached. Wait a minute and try again.")

def cosine(a,b):
    """Return the cosine similarity of two vectors, from -1 to 1.

    1 means they point the same way (very similar meaning), 0 unrelated."""

    dot_product = sum(x*y for x,y in zip(a,b))
    length_a = math.sqrt(sum(x*x for x in a))
    length_b = math.sqrt(sum(y*y for y in b))
    return dot_product / (length_a * length_b)

def retrieve(query, k=3):
    """Find the k chunks most similar to the question.

    Embeds the question, scores every chunk with cosine similarity,
    and returns the top k as dicts with id, heading, text and score,
    highest score first.
    """

    embed = embed_prompt(query)
    scores = {}
    for i, e in enumerate(embeddings):
        scores[i] = cosine(e["embedding"],embed)
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    results = []
    for i, score in ranked[:k]:
        chunk = embeddings[i]
        results.append({"id":chunk["id"], "heading":chunk["heading"], "text": chunk["text"], "score": round(score, 4)})
    return results

if __name__ == "__main__":
    query = str(input("Question: "))
    for r in retrieve(query):
        print(r["score"], r["id"], "|", r["heading"])
    from collections import Counter
    dupes = [i for i, n in Counter(c["id"] for c in embeddings).items() if n > 1]
    print(len(dupes), dupes[:10])