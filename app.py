from dotenv import load_dotenv
from retriever import retrieve, formatted_string
from llm import answer, FALLBACK_MESSAGE
import time

load_dotenv()

def main(query):
    try:
        chunks = retrieve(query)
        if not chunks:
            print(FALLBACK_MESSAGE)
        else:
            result = answer(query, formatted_string(chunks))
            print(result)
            print("\nSources:")
            if result != FALLBACK_MESSAGE:
                for c in chunks:
                    print(f"{c['score']:.2f}  {c['id']}  {c['heading']}")
    except RuntimeError as e:
        print(e)

if __name__ == "__main__":
    TURNS = 3
    current_turn = 0
    while True:
        if current_turn == TURNS:
            time.sleep(60)
            current_turn = 0
        else:
            query = str(input("Question: (or exit) "))
            if query.lower() in ("exit","quit","q",""):
                break
            current_turn += 1
            main(query)