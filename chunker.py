import json
import re
from collections import Counter
from pathlib import Path
import sys
import unicodedata

FIRST_CONTENT_PAGE = 38
LAST_CONTENT_PAGE = 385
TABLE_MARKER = r"MATRIX\s+OF\s+TOPICS\s+VS\.\s+REFERENCE\s+MATERIAL"
CHAPTER_PATTERN = re.compile(r"^CHAPTER\s(?P<num>\d+)\n(?P<title>[A-Z].+)$", re.MULTILINE)
SECTION_PATTERN = re.compile(r"^(\d+(?:\.\d+)*\.)\s+([A-Z].+)$", re.MULTILINE)
START_TABLE = "T ABLE I.1. THE 18 SWEBOK KAS"
CHUNK_SIZE = 1500
OVERLAP = 150
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
    full_text = unicodedata.normalize("NFKC", full_text)
    return full_text.replace(" -\n","")

def remove_tables(full_text):
    """Remove each chapter's topics-vs-references table, from its title up to the next chapter."""
    headings = list(CHAPTER_PATTERN.finditer(full_text))
    chapter_starts = [h.start() for h in headings]
    matrix_starts = [m.start() for m in re.finditer(TABLE_MARKER,full_text)]
    cuts = []
    for start in matrix_starts:
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

def remove_intro_table(full_text):
    """Remove Table I.1 (the list of KAs) from the introduction.

    The table starts at START_TABLE and ends after the item whose number
    equals the chapter count (18 for SWEBOK). Its rows look like section
    headings, so leaving them in would create false section matches."""

    start = full_text.find(START_TABLE)
    assert start != -1, f"Intro table start not found: {START_TABLE!r}"
    n= len(list(CHAPTER_PATTERN.finditer(full_text)))
    end = None
    for m in SECTION_PATTERN.finditer(full_text):
        if m.start() > start and m.group(1) == f"{n}.":
            end = m.end()
            break
    assert end is not None, f"Intro table end (item {n}.) not found"

    cleaned = full_text[:start] + full_text[end:]
    return cleaned

def split_by_size(text, size, overlap):
    """Split text into parts of up to `size` characters.

    Each part after the first repeats the last `overlap` characters
    of the previous part. Returns a list of strings."""

    chunks = []
    for i in range(0,len(text),size-overlap):
        chunks.append(text[i:i+size])
        if i+size >= len(text):
            break
    return chunks
    
def build_chunks(text):
    """Build the chunk list from the cleaned text.

    The introduction (before CHAPTER 01) is split by size. After that,
    each chapter's opening text and each section become one chunk,
    split into -p1, -p2 parts when longer than CHUNK_SIZE.
    Returns a list of dicts with id, chapter, heading and text."""
    
    chapters = list(CHAPTER_PATTERN.finditer(text))
    assert chapters, "No chapters found. Check CHAPTER_PATTERN."
    first = chapters[0].start()
    chunks = []
    for k, part in enumerate(split_by_size(text[:first],CHUNK_SIZE,OVERLAP), start=1):
        chunks.append({"id": f"intro-p{k}", "chapter": 0, "heading": "Introduction", "text": part})
    sections = [m for m in SECTION_PATTERN.finditer(text) if m.start() >= first]
    boundaries = sorted([(m.start(),"chapter",m) for m in chapters] +
                         [(m.start(),"section",m) for m in sections],
                         key= lambda b: b[0],)
    
    current_chapter = None
    for i, (position, kind, m) in enumerate(boundaries):
        end = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(text)
        piece = text[position:end]

        if kind == "chapter":
            current_chapter = int(m.group("num"))
            base_id = f"ch{current_chapter:02d}-intro"
            heading = m.group("title")
        else:
            base_id = f"ch{current_chapter:02d}-{m.group(1)}"
            heading = m.group().strip()

        if len(piece) > CHUNK_SIZE:
            parts = split_by_size(piece, CHUNK_SIZE, OVERLAP)
            for k, part in enumerate(parts,start=1):
                chunk = ({
                    "id" : f"{base_id}-p{k}",
                    "chapter" : current_chapter,
                    "heading" : heading,
                    "text" : part
                })
                chunks.append(chunk)
        else:
            chunks.append({
                "id" : base_id,
                "chapter" : current_chapter,
                "heading" : heading,
                "text" : piece
            })
            
    return chunks


def save_text(name, text, folder="debug"):
    """Save a string to `folder/name` as UTF-8, creating the folder if needed."""
    path = Path(folder)
    path.mkdir(parents=True, exist_ok=True)
    (path / name).write_text(text, encoding="utf-8")

def save_json(name, data, folder: str | Path = "debug", indent: int | None = 2):
    """Save data as JSON to `folder/name`, creating the folder if needed.

    Use indent=2 for files people read, and indent=None for large files
    only programs read (such as embeddings), to keep them small."""
    path = Path(folder)
    path.mkdir(parents=True, exist_ok=True)
    with open(path / name, "w", encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False, indent=indent) 

if __name__ == '__main__':
    with open("pages.json", encoding="utf-8") as f:
        raw = json.load(f)
    content = keep_content_pages(raw, FIRST_CONTENT_PAGE, LAST_CONTENT_PAGE)
    removed_header = clean_pages(content)
    if DEBUG:
        save_json("removed_header.json",removed_header, "debug/software_engineering")
    join_text = join_pages(removed_header)
    if DEBUG:
        save_text("join_text.txt",join_text, "debug/software_engineering")
    cleaned_text = remove_tables(join_text)
    if DEBUG:
        save_text("cleaned_text.txt",cleaned_text, "debug/software_engineering")
    intro_cleaned = remove_intro_table(cleaned_text)
    if DEBUG:
        save_text("intro_cleaned.txt",intro_cleaned, "debug/software_engineering")
    chunks = build_chunks(intro_cleaned)
    print([len(chunk["text"]) for chunk in chunks[:5]])
    print(chunks[0]["id"], chunks[1]["id"], chunks[-1]["id"])
    save_json("chunks.json",chunks,folder="data/software_engineering")