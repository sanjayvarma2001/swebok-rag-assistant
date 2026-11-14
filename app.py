import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()
response = requests.post(
    "https://ai.mongodb.com/v1/embeddings",
    headers={"Authorization": f"Bearer {os.environ['VOYAGE_API_KEY']}"},
    json={"input": ["Sample text 1","Sample text 2"], "model": "voyage-4", "input_type": "document"},
    timeout=30,
)

def chunk_by_words(text, size, overlap=30):
    words =text.split()
    step = size-overlap
    return [" ".join(words[i:i+size]) for i in range(0,len(words),step)]
