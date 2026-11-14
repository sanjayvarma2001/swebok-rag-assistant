from google import genai
from google.genai import errors
import os
from dotenv import load_dotenv

load_dotenv()
llm_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=llm_key)

def respond(request: str, extracted_data: str):
    prompt = f"""# TODO: system_instruction, page citations, stronger rules
    You are an Software Engineer Assistant. You help users in understand the software engineering concepts provide in the {extracted_data}.
    rules: 
        - Take user's {request} and extracted data to generate the answer
        - If extracted data doesn't match to users prompt. Don't hallucinate say 'I don't know at the momment I'm working on it'
    """
    try:
        response = client.models.generate_content(model="gemini-2.5-flash",contents=prompt)
        return response.text
    except errors.APIError as e:
        print(f"Gemini Error: {e}")
        return "AI analysis currently unavailable, but your data was saved."

