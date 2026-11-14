from pypdf import PdfReader
import json

PDF_PATH = "docs/swebok.pdf"

def load_pdf_pages():
    reader = PdfReader(PDF_PATH)
    page_data = {}
    for i in range(len(reader.pages)):
        text = reader.pages[i].extract_text()
        page_data[i+1] = text
    return page_data

if __name__ == "__main__":
    pages = load_pdf_pages()
    with open("pages.json","w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)