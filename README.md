# Software Engineer Assistant - Chat Bot

A chatbot that helps junior developers and students learn software engineering concepts. It answers questions using only the SWEBOK Guide (v4.0a) and cites the page each answer comes from.

It’s built with retrieval-augmented generation (RAG): the guide is split into sections and embedded once, and each question retrieves the most relevant sections before Gemini writes the answer.

> Status: work in progress. PDF loading and cleaning work; retrieval and answers are next.

## How it works

The project has two parts: **indexing**, which runs once, and **answering**, which runs for every question.

### 1. Indexing (run once)

1. **Load:** read the PDF page by page and save each page's text by page number to `pages.json`.
2. **Filter:** keep only the content pages (introduction to the last chapter), skipping the table of contents, references and appendices.
3. **Clean:** remove the running header from each page and rejoin words split across lines.
4. **Chunk:** join the pages into one text and split it by section (e.g. "4.2 Unit Testing"), keeping the page numbers for each chunk.
5. **Embed:** convert each chunk into a 1024-number vector with Voyage AI and save the text, pages and vector to `chunks.json`.

### 2. Answering (every question)

1. **Embed the question** with the same Voyage model.
2. **Retrieve:** compare it with every chunk using cosine similarity and take the 3 closest.
3. **Generate:** send the question and those chunks' text to Gemini, with instructions to answer only from that text and cite the pages.
4. If the answer isn't in the retrieved sections, the assistant says it doesn't know instead of guessing.

## Tech stack

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
4. Download the SWEBOK Guide v4.0a, save it as docs/swebok.pdf
5. Create .env with GEMINI_API_KEY and VOYAGE_API_KEY

## Usage
1. python pdf_loader.py   → creates pages.json
2. python chunker.py      → filters and cleans pages (work in progress)

## Design decisions

- **Raw text is saved once and never changed.** `pdf_loader.py` writes each page's text to `pages.json`, and cleaning happens in a separate step. Cleaning takes several tries; this way each attempt re-runs in seconds without re-reading the PDF, and a mistake never damages the original.

- **The first line of every page is removed.** It is always the running header (`SWEBOK® GUIDE V4.0a` or the chapter title, with the page number). This was checked against the data, not assumed: all 348 content pages have a header on line 1, including the introduction's roman-numeral pages.

- **The table of contents, reference lists and appendices are skipped.** The table of contents lists every section title, so it matches almost any question but contains no answers. Reference lists are mostly names and titles. Both would push useless chunks into the top results.

- **Words split across lines are rejoined.** `"pro -\nduces"` becomes `"produces"`. Only that exact pattern (a space, a hyphen and a line break) is joined, so real hyphens such as `"two- or three-level"` are kept.

- **Chunks follow sections, not a fixed size** *(planned)*. Sections are natural units of meaning, and the section number (e.g. 4.2) gives each chunk an ID and a clear citation. Long sections are split further, with the heading repeated in each piece so no piece loses its context.

- **Pages are joined before chunking** *(planned)*. Sections often run across a page break, and chunking page by page would cut them in half. The position where each page starts is recorded, so every chunk still knows its page numbers.

- **A JSON file instead of a vector database** *(planned)*. A few hundred chunks can be compared one by one in milliseconds. A vector database with an approximate-nearest-neighbour index (such as pgvector or Chroma) becomes worthwhile at tens of thousands of chunks.

- **Answers come only from the retrieved text, with page citations** *(planned)*. Grounding the model in the guide reduces made-up answers. If the answer isn't in the retrieved sections, the assistant says it doesn't know.

## Roadmap

- [x] PDF loading
- [x] Page filtering and header cleaning
- [ ] Section-based chunking
- [ ] Embeddings
- [ ] Retrieval with cosine similarity
- [ ] Answers with page citations
- [ ] Evaluation with 10 test questions
- [ ] Hybrid search (BM25 + vectors)
- [ ] Later: FastAPI endpoint and a web UI
