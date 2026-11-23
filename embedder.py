from dotenv import load_dotenv
import voyageai
import os
from pathlib import Path
import json
import time
from voyageai.error import RateLimitError
from chunker import save_json

load_dotenv()

VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")

assert VOYAGE_API_KEY, "VOYAGE_API_KEY missing from .env"

vo = voyageai.Client()

DATA_DIR = Path("data/software_engineering")
CHUNKS_PATH = DATA_DIR / "chunks.json"
EMBEDDINGS_PATH = DATA_DIR / "embeddings.json"


def embed_chunk(batch):
    """Embed one batch of chunks with Voyage and add each vector to its chunk.

    Sends the batch's texts in one request (input_type="document") and
    stores each 1024-number vector under the chunk's "embedding" key.
    Returns the same batch, updated in place."""

    texts = [c["text"] for c in batch]
    vectors = vo.embed(texts,model="voyage-4",input_type="document")
    for chunk, vector in zip(batch,vectors.embeddings):
        chunk["embedding"] = vector
    return batch

def embed_all(chunks, size, retries = 5):
    """Embed all chunks in batches of `size`, one batch per minute.

    The pause keeps each minute under Voyage's free limit of 10,000 tokens.
    A rate-limited batch waits 60 seconds and retries, up to `retries` times,
    then raises RuntimeError. Returns the chunks with embeddings added."""

    for start in range(0, len(chunks), size):
        batch = chunks[start:start+size]
        for attempt in range(1,retries+1):
            try:
                embed_chunk(batch)
                break
            except RateLimitError:
                print(f"rate limited, waiting 60s (attempt {attempt}/{retries})")
                time.sleep(60)
        else:
            raise RuntimeError(f"Batch at {start} failed after {retries} attempts")
        print(f"batch {start // size + 1} done")
        if start + size < len(chunks):
            time.sleep(60)

    return chunks

if __name__ == "__main__":
    with open(CHUNKS_PATH,encoding="utf-8") as f:
        chunks = json.load(f)
    expected = len(chunks)
    result = embed_all(chunks,25)
    assert len(result) == expected, f"{len(chunks)} chunks, expected {expected}"
    assert all(len(c.get("embedding", [])) == 1024 for c in chunks), "Missing or wrong-size embedding"
    print(len(chunks), "chunks embedded")
    save_json("embeddings.json", result, folder=DATA_DIR, indent=None)