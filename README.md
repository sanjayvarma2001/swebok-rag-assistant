# Software Engineer Assistant - Chat Bot

A chatbot that helps junior developers and students learn software engineering concepts. It answers questions using only the SWEBOK Guide (v4.0a) and cites the chapter and section each answer comes from.

It's built with retrieval-augmented generation (RAG): the guide is split into sections and embedded once, and each question retrieves the most relevant sections before Gemini writes the answer.

> Status: work in progress. The indexing pipeline now produces [N] chunks from 18 chapters and [S] sections, saved to `chunks.json`. Embeddings, retrieval and answers are next.

## How it works

The project has two parts: **indexing**, which runs once, and **answering**, which runs for every question.

### 1. Indexing (run once)

1. **Load:** read the PDF page by page and save each page's text by page number to `pages.json`.
2. **Filter:** keep only the content pages (introduction to the last chapter), skipping the table of contents, references and appendices.
3. **Clean:** remove the running header from each page, normalise special characters such as ligatures, and rejoin words split across lines.
4. **Remove tables:** delete the 18 "Matrix of Topics vs. Reference Material" tables and the introduction's list of KAs. Their rows look like section headings, so they would create duplicate headings and false matches.
5. **Chunk:** split the introduction by size, then make one chunk per chapter opening and per section, with IDs such as `ch04-4.2.`. Long sections are split into parts (`ch04-4.2.-p1`, `-p2`).
6. **Embed:** convert each chunk into a 1024-number vector with Voyage AI and save the text, IDs and vector to `embeddings.json` *(planned)*.

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
| Storage | JSON files (`pages.json`, `chunks.json`, `embeddings.json`) |
| Configuration | python-dotenv |

## Setup

1. Clone and enter the repo
2. Create and activate a virtual environment (Windows / macOS-Linux)
3. Install requirements
4. Download the SWEBOK Guide v4.0a, save it as `docs/swebok.pdf`
5. Create `.env` with `GEMINI_API_KEY` and `VOYAGE_API_KEY`

## Usage

1. `python pdf_loader.py` → creates `pages.json`
2. `python chunker.py` → cleans the text and writes `data/software_engineering/chunks.json`
   - Add `--debug` to also save each cleaning step to `debug/software_engineering/` for inspection.

## Design decisions

- **Raw text is saved once and never changed.** `pdf_loader.py` writes each page's text to `pages.json`, and cleaning happens in a separate step. Cleaning takes several tries; this way each attempt re-runs in seconds without re-reading the PDF, and a mistake never damages the original.

- **The first line of every page is removed.** It is the running header (`SWEBOK® GUIDE V4.0a` or the chapter title, with the page number). The introduction's roman-numeral pages follow the same pattern.

- **The table of contents, reference lists and appendices are skipped.** The table of contents lists every section title, so it matches almost any question but contains no answers. Reference lists are mostly names and titles. Both would push useless chunks into the top results.

- **Ligatures are normalised.** The PDF stores some letter pairs as single characters (`ﬁ`, `ﬂ`), so `Speciﬁcation` and `Specification` look the same but don't match in code. Unicode NFKC normalisation replaces them with plain letters and keeps the case.

- **Words split across lines are rejoined.** `"pro -\nduces"` becomes `"produces"`. Only that exact pattern (a space, a hyphen and a line break) is joined, so real hyphens such as `"two- or three-level"` are kept.

- **Tables are removed by position, not by text.** Each matrix table starts at its title and ends where the next chapter begins. Matching repeated text would miss rows, because pypdf puts each table cell on its own line and the reference codes differ between rows. The introduction's list of KAs is removed the same way: it ends at the item whose number equals the chapter count.

- **Tables with real content and figures are kept, for now.** Tables that explain concepts hold useful text, and figure labels don't create false headings. Retrieval tests will show whether either needs cleaning.

- **Chunks follow sections, not a fixed size.** Sections are natural units of meaning, and the chapter and section numbers give each chunk an ID and a clear citation. Positions are used as cut points: each chunk runs from its heading to the next chapter or section heading, so no section runs into the next chapter.

- **Long sections are split at 1,500 characters with 150 characters of overlap.** The overlap keeps an idea that crosses a cut in both parts. The size is a starting value to be tuned with evaluation results.

- **The introduction is chunked by size.** Its numbered lists aren't sections, so it is split off before section detection and divided into parts (`intro-p1`, `intro-p2`).

- **Citations use section IDs, not page numbers.** Section numbers restart in each chapter, so a chapter-and-section ID is the reliable reference. Page numbers are a possible later addition.

- **A JSON file instead of a vector database.** About a thousand chunks can be compared one by one in milliseconds. A vector database (such as pgvector) becomes worthwhile when the app is deployed or the data grows to tens of thousands of chunks.

- **Generated data isn't committed.** `pages.json`, `chunks.json` and the debug files contain the guide's text, so they stay out of the repository. Running the scripts rebuilds them.

- **Answers come only from the retrieved text, with section citations** *(planned)*. Grounding the model in the guide reduces made-up answers. If the answer isn't in the retrieved sections, the assistant says it doesn't know.

## Roadmap

- [x] PDF loading
- [x] Page filtering and header cleaning
- [x] Ligature normalisation
- [x] Table removal (18 matrix tables and the introduction's KA list)
- [x] Chapter and section detection
- [x] Section-based chunks with chapter IDs and size splitting
- [ ] Merge very short chunks and repeat headings in split parts
- [ ] Embeddings (Voyage AI)
- [ ] Retrieval with cosine similarity
- [ ] Answers with section citations
- [ ] Evaluation with 10 test questions
- [ ] Hybrid search (BM25 + vectors)
- [ ] Later: FastAPI endpoint, pgvector and a web UI