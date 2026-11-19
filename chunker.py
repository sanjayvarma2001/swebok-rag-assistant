import json
import re
from collections import Counter
from pathlib import Path
import sys

with open("pages.json", encoding="utf-8") as f:
    raw = json.load(f)

FIRST_CONTENT_PAGE = 38
LAST_CONTENT_PAGE = 385
TABLE_MARKER = r"MATRIX\s+OF\s+TOPICS\s+VS\.\s+REFERENCE\s+MATERIAL"
CHAPTER_PATTERN = re.compile(r"^CHAPTER\s(?P<num>\d+)\n(?P<title>[A-Z].+)$", re.MULTILINE)
SECTION_PATTERN = re.compile(r"^(\d+(?:\.\d+)*\.)\s+([A-Z].+)$", re.MULTILINE)
DEBUG_DIR = Path("debug")
DEBUG = "--debug" in sys.argv

def keep_content_pages(pages, start, end):
    """Content Pages extraction needs parameters - pages (json formatted), start page, end page"""
    cleaned_pages = {int(k):v for k,v in pages.items() if start <= int(k) <= end}
    return cleaned_pages

def clean_pages(pages):
    """Removing first line of each page as it is a header of each page"""
    cleaned = {}
    for page, text in pages.items():
        lines = text.splitlines()[1:]
        text = "\n".join(lines)
        cleaned[page] = text
    return cleaned

def join_pages(pages):
    """Joining all pages and removing hyphen and next line words """
    full_text = "\n".join(pages.values())
    return full_text.replace(" -\n","")

def remove_tables(full_text):
    """Remove each chapter's topics-vs-references table, from its title up to the next chapter."""
    headings = list(CHAPTER_PATTERN.finditer(full_text))
    chapter_starts = [h.start() for h in headings]
    matrix_start = [m.start() for m in re.finditer(TABLE_MARKER,full_text)]
    cuts = []
    for start in matrix_start:
        end = next((c for c in chapter_starts if c > start), len(full_text))
        cuts.append((start,end))
    pieces = []
    prev=0
    for start, end in cuts:
        pieces.append(full_text[prev:start])
        prev=end
    pieces.append(full_text[prev:])
    cleaned = "".join(pieces)
    return cleaned

def save_text(name, text, folder="debug"):
    path = Path(folder)
    path.mkdir(parents=True, exist_ok=True)
    (path / name).write_text(text, encoding="utf-8")

def save_json(name, data, folder="debug"):
    path = Path(folder)
    path.mkdir(parents=True, exist_ok=True)
    with open(path / name, "w", encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False, indent=2) 

if __name__ == '__main__':
    content = keep_content_pages(raw, FIRST_CONTENT_PAGE, LAST_CONTENT_PAGE)
    print(len(content), min(content), max(content))
    removed_header = clean_pages(content)
    if DEBUG:
        save_json("removed_header.json",removed_header, "data/Software Engineering")
    join_text = join_pages(removed_header)
    if DEBUG:
        save_text("join_text.txt",join_text, "debug/Software Engineering")
    cleaned_text = remove_tables(join_text)
    if DEBUG:
        save_text("cleaned_text.txt",cleaned_text, "debug/Software Engineering")
    """Debugging"""
    print(len(join_text), len(cleaned_text))
    print(cleaned_text.count("MATRIX OF TOPICS"))
    print(len(list(re.finditer(TABLE_MARKER, join_text))))

    sections = list(SECTION_PATTERN.finditer(cleaned_text))
    counts = Counter(m.group(0).strip() for m in sections)
    print(len(sections), sum(1 for n in counts.values() if n > 1))