import voyageai
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")

assert VOYAGE_API_KEY, "VOYAGE_API_KEY missing from .env"

EMBED_MODEL = "voyage-4"
voyage_client = voyageai.Client(api_key=VOYAGE_API_KEY)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"

gemini_client = genai.Client(api_key=GEMINI_API_KEY,
                             http_options=types.HttpOptions(api_version="v1beta"),)