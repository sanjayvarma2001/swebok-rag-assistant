import json

with open("pages.json", encoding="utf-8") as f:
    raw = json.load(f)

FIRST_CONTENT_PAGE = 38
LAST_CONTENT_PAGE = 385

def keep_content_pages(pages, start, end):
    cleaned_pages = {int(k):v for k,v in pages.items() if start <= int(k) <= end}
    return cleaned_pages

def clean_pages(pages):
    for page, text in pages.items():
        lines = text.splitlines()[1:]
        text = "\n".join(lines)
        text = text.replace(" -\n","")
        pages[page] = text
    return " "
    

if __name__ == '__main__':
    content = keep_content_pages(raw, FIRST_CONTENT_PAGE, LAST_CONTENT_PAGE)
    print(len(content), min(content), max(content))
    clean_pages(content)
    print(content[50][:300])