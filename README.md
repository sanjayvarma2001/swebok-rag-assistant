# Software Engineer Assistant - Chat Bot

A chatbot that helps junior developers and students learn software engineering concepts. It answers questions using only the SWEBOK Guide (v4.0a) and cites the chapter and section each answer comes from.

It's built with retrieval-augmented generation (RAG): the guide is split into sections and embedded once, and each question retrieves the most relevant sections before Gemini writes the answer.

> Status: work in progress. Loading, header removal, hyphen rejoining and table removal work. The guide has 18 chapters and 796 sections. Chunking, embeddings and answers are next.

## How it works

The project has two parts: **indexing**, which runs once, and **answering**, which runs for every question.

### 1. Indexing (run once)

1. **Load:** read the PDF page by page and save each page's text by page number to `pages.json`.
2. **Filter:** keep only the content pages (introduction to the last chapter), skipping the table of contents, references and appendices.
3. **Clean:** remove the running header from each page and rejoin words split across lines.
4. **Remove tables:** delete the 18 "Matrix of Topics vs. Reference Material" tables. Their rows repeat section titles, so they would create duplicate headings and false matches.
5. **Chunk:** split the text by section (e.g. "4.2 Unit Testing") and give each chunk an ID such as `ch04-4.2.` *(planned)*.
6. **Embed:** convert each chunk into a 1024-number vector with Voyage AI and save the text, IDs and vector to `chunks.json` *(planned)*.

### 2. Answering (every question)

1. **Embed the question** with the same Voyage model.
2. **Retrieve:** compare it with every chunk using cosine similarity and take the 3 closest.
3. **Generate:** send the question and those chunks' text to Gemini, with instructions to answer only from that text and cite the section IDs.
4. If the answer isn't in the retrieved sections, the assistant says it doesn't know instead of guessing.

## Tech stack

| Purpose | Tool |
| --- | --- |
| Language | Python |
| PDF text extraction | pypdf |
| Embeddings | Voyage AI (`voyage-4`, via `requests`) |
| Answer generation | Google Gemini (`google-genai`) |
| Storage | JSON files (`pages.json`, `chunks.json`) |
| Configuration | python-dotenv |

## Setup

1. Clone and enter the repo
2. Create and activate a virtual environment (Windows / macOS-Linux)
3. Install requirements
4. Download the SWEBOK Guide v4.0a, save it as `docs/swebok.pdf`
5. Create `.env` with `GEMINI_API_KEY` and `VOYAGE_API_KEY`

## Usage

1. `python pdf_loader.py` → creates `pages.json`
2. `python chunker.py` → cleans the text and prints the chapter and section counts (work in progress)

## Design decisions

- **Raw text is saved once and never changed.** `pdf_loader.py` writes each page's text to `pages.json`, and cleaning happens in a separate step. Cleaning takes several tries; this way each attempt re-runs in seconds without re-reading the PDF, and a mistake never damages the original.

- **The first line of every page is removed.** It is the running header (`SWEBOK® GUIDE V4.0a` or the chapter title, with the page number). The introduction's roman-numeral pages follow the same pattern.

- **The table of contents, reference lists and appendices are skipped.** The table of contents lists every section title, so it matches almost any question but contains no answers. Reference lists are mostly names and titles. Both would push useless chunks into the top results.

- **Words split across lines are rejoined.** `"pro -\nduces"` becomes `"produces"`. Only that exact pattern (a space, a hyphen and a line break) is joined, so real hyphens such as `"two- or three-level"` are kept.

- **Tables are removed by position, not by text.** Each table starts at the "MATRIX OF TOPICS VS. REFERENCE MATERIAL" title and ends where the next chapter begins. Matching repeated text would miss rows, because pypdf puts each table cell on its own line and the reference codes differ between rows. The step checks that exactly 18 tables are found, so a wrong PDF fails loudly instead of quietly.

- **Chunks follow sections, not a fixed size** *(planned)*. Sections are natural units of meaning, and the chapter and section numbers give each chunk an ID and a clear citation. Long sections are split further, with the heading repeated in each piece so no piece loses its context.

- **Citations use section IDs, not page numbers.** Section numbers restart in each chapter, so a chapter-and-section ID is the reliable reference. Page numbers are a possible later addition.

- **Pages are joined before chunking** *(planned)*. Sections often run across a page break, and chunking page by page would split them in half.

- **A JSON file instead of a vector database** *(planned)*. A few hundred chunks can be compared one by one in milliseconds. A vector database with an approximate-nearest-neighbour index (such as pgvector or Chroma) becomes worthwhile at tens of thousands of chunks.

- **Answers come only from the retrieved text, with section citations** *(planned)*. Grounding the model in the guide reduces made-up answers. If the answer isn't in the retrieved sections, the assistant says it doesn't know.

## Roadmap

- [x] PDF loading
- [x] Page filtering and header cleaning
- [x] Table removal (18 tables)
- [x] Chapter and section detection (18 chapters, 796 sections)
- [ ] Section-based chunks with size limits
- [ ] Embeddings (Voyage AI)
- [ ] Retrieval with cosine similarity
- [ ] Answers with section citations
- [ ] Evaluation with 10 test questions
- [ ] Hybrid search (BM25 + vectors)
- [ ] Later: FastAPI endpoint and a web UI