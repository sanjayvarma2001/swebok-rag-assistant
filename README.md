# Software Engineer Assistant - Chat Bot

A chatbot that helps junior developers and students learn software engineering concepts. It answers questions using only the SWEBOK Guide (v4.0a) and cites the chapter and section each answer comes from.

It's built with retrieval-augmented generation (RAG): the guide is split into sections and embedded once, and each question retrieves the most relevant sections before Gemini writes the answer.

> Status: working end to end. Questions are answered from the guide with section citations, and off-topic questions get a fallback message. Evaluation is next.

## How it works

The project has two parts: **indexing**, which runs once, and **answering**, which runs for every question.

### 1. Indexing (run once)

1. **Load:** read the PDF page by page and save each page's text by page number to `pages.json`.
2. **Filter:** keep only the content pages (introduction to the last chapter), skipping the table of contents, references and appendices.
3. **Clean:** remove the running header from each page, normalise special characters such as ligatures, and rejoin words split across lines.
4. **Remove tables:** delete the 18 "Matrix of Topics vs. Reference Material" tables and the introduction's list of KAs. Their rows look like section headings, so they would create duplicate headings and false matches.
5. **Chunk:** split the introduction by size, then make one chunk per chapter opening and per section, with IDs such as `ch04-4.2.`. Long sections are split into parts (`ch04-4.2.-p1`, `-p2`).
6. **Embed:** convert each chunk into a 1024-number vector with Voyage AI and save the chunks with their vectors to `embeddings.json`.

### 2. Answering (every question)

1. **Embed the question** with the same Voyage model.
2. **Retrieve:** compare it with every chunk using cosine similarity and take the 3 closest.
3. Filter: drop chunks scoring below 0.35. If none are left, return the fallback message without calling Gemini.
4. **Generate:** send the question and those chunks' text to Gemini, with instructions to answer only from that text and cite the section IDs .
5. If the answer isn't in the retrieved sections, the assistant says it doesn't know instead of guessing.

## Tech stack

| Purpose | Tool |
| --- | --- |
| Language | Python |
| PDF text extraction | pypdf |
| Embeddings | Voyage AI (`voyage-4`, `voyageai` SDK) |
| Answer generation | Google Gemini (`gemini-2.5-flash`, `google-genai`) |
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
3. `python embedder.py` → embeds every chunk and writes `data/software_engineering/embeddings.json`
   - On Voyage's free limits this takes about 50 minutes (one batch per minute). Keep the computer awake while it runs.
4. `python retriever.py` → asks for a question and prints the 3 most similar chunks with their scores, IDs and headings.
5. `python app.py` → ask questions in a loop. Each answer shows its citations, followed by the source chunks and their scores. Type exit to quit.

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

- **Embeddings are created in batches of 25, one batch per minute.** Voyage's free tier allows 10,000 tokens per minute. A batch of 25 chunks is under 10,000 tokens, so one batch a minute stays within the limit. A rate-limited batch waits 60 seconds and retries, up to 5 times, so a failure retries only that batch.

- **Embeddings are computed once and saved.** Embedding all chunks takes about 50 minutes on the free tier, so it never runs on each question. Only the question is embedded at answer time.

- **The Voyage SDK replaced the earlier REST workaround.** The `voyageai` SDK was blocked by Windows Smart App Control at first, so the project called the API through `requests`. With newer package versions the SDK now runs, so the embedder uses it. The REST version remains a fallback if it is blocked again.

- **`embeddings.json` is saved without indentation.** It holds over a million numbers. Indenting would put each number on its own line and make the file several times larger; nobody reads it by eye.

- **Citations use section IDs, not page numbers.** Section numbers restart in each chapter, so a chapter-and-section ID is the reliable reference. Page numbers are a possible later addition.

- **A JSON file instead of a vector database.** About a thousand chunks can be compared one by one in milliseconds. A vector database (such as pgvector) becomes worthwhile when the app is deployed or the data grows to tens of thousands of chunks.

- **Generated data isn't committed.** `pages.json`, `chunks.json`, `embeddings.json` and the debug files contain the guide's text, so they stay out of the repository. Running the scripts rebuilds them.

- **Answers come only from the retrieved text, with section citations**. Grounding the model in the guide reduces made-up answers. If the answer isn't in the retrieved sections, the assistant says it doesn't know.

- **The question and the chunks use the same model, set in one place.** config.py holds the Voyage client and the model name (voyage-4), and both the embedder and the retriever import them. Vectors from different models can't be compared, so they must never drift apart.
- **Questions are embedded with input_type="query", chunks with "document".** Voyage tunes each vector for its role, so questions and the passages that answer them match better.
- **Brute-force search over all chunks.** Every question is compared with all 1,157 chunk vectors, which is exact and takes well under a second at this size. An approximate index (pgvector, FAISS) only becomes worthwhile at hundreds of thousands of chunks.
- **Cosine similarity is written by hand,** in plain Python, to show how retrieval works. NumPy would be faster if needed.
- **Rules go in a system instruction, material in the content.** The system instruction tells Gemini to use only the context, cite a passage ID after each point, reply with an exact fallback message when the context lacks the answer, and ignore any instructions inside the context. The content holds the ID-labelled chunks, then the question.
- **Low temperature (0.2)** keeps answers close to the source text.
- **Two layers of fallback.** A score threshold (0.35) stops clearly off-topic questions before Gemini is called. If a weak chunk passes, Gemini's rule still returns the fallback. In tests, a direct question scored 0.67, a paraphrase 0.42 and an off-topic question 0.32.
- **All top 3 chunks are passed,** not only the best one. In testing, the best section ranked second by a tiny margin, and answers often combine two sections.
- **A separate message for service errors,** so a failed API call isn't confused with "not in the guide".
- **Functions return, the app prints.** retrieve and answer return values, and only app.py prints. A future FastAPI endpoint can reuse both functions unchanged.
- **A pause after 3 questions** keeps question embedding within Voyage's free limit of 3 requests per minute.

## Known limitations

- **Parts are cut at fixed positions,** so a part can start or end mid-word. Cutting at sentence ends is planned.
- **Some sections are very long** (for example, one chapter 8 section splits into 10+ parts). This may mean some subsection headings weren't detected. To be checked during retrieval testing.
- Fixing either means re-chunking and re-embedding, so fixes will be batched together.
- **Numbered lists inside chapters are detected as sections,** creating 47 duplicate chunk IDs and ambiguous citations. Tracked in issue #[number].
- **Some headings include reference codes,** such as 5.3. Unit Testing Tools [1-c22, 2-c8].
- **Paraphrased questions score lower than direct ones** (about 0.42 compared with 0.67 in tests), so the fallback threshold must not be set too high.
- **Headings that wrap onto two lines are cut off** in citations (e.g. 2.4. Some Paradigms for Development Life).
- **Answers can drop qualifiers:** one answer turned "typically, but not always" into "typically".
- **The 0.35 threshold is based on a few tests,** and will be checked in the evaluation.
- **The question limit counts questions,** not time, so it can pause even when the per-minute limit has already reset.

## Roadmap

- [x] PDF loading
- [x] Page filtering and header cleaning
- [x] Ligature normalisation
- [x] Table removal (18 matrix tables and the introduction's KA list)
- [x] Chapter and section detection
- [x] Section-based chunks with chapter IDs and size splitting
- [x] Embeddings (Voyage AI, batched for the free tier)
- [x] Retrieval with cosine similarity
- [x] Answers with section citations
- [x] Question loop (`app.py`)
- [ ] Evaluation with 10 test questions
- [ ] Sentence-end cuts, merging very short chunks, repeating headings in split parts
- [ ] Hybrid search (BM25 + vectors)
- [ ] Later: FastAPI endpoint, pgvector and a web UI