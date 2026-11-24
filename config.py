import voyageai
import os
from dotenv import load_dotenv
load_dotenv()

VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")

assert VOYAGE_API_KEY, "VOYAGE_API_KEY missing from .env"

EMBED_MODEL = "voyage-4"
voyage_client = voyageai.Client(api_key=VOYAGE_API_KEY)