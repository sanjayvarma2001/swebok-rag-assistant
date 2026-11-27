# Design decisions

Why the project is built the way it is, stage by stage, followed by its known limitations.

## Loading and cleaning

- **Raw text is saved once and never changed.** `pdf_loader.py` writes each page's text to `pages.json`, and cleaning happens in a separate step. Cleaning takes several tries; this way each attempt re-runs in seconds without re-reading the PDF, and a mistake never damages the original.

- **The first line of every page is removed.** It is the running header (`SWEBOK® GUIDE V4.0a` or the chapter title, with the page number).

- **The table of contents, reference lists and appendices are skipped.** The table of contents lists every section title, so it matches almost any question but contains no answers. Reference lists are mostly names and titles. Both would push useless chunks into the top results.

- **Ligatures are normalised.** The PDF stores some letter pairs as single characters (`ﬁ`, `ﬂ`), so `Speciﬁcation` and `Specification` look the same but don't match in code. Unicode NFKC normalisation replaces them with plain letters and keeps the case.

- **Words split across lines are rejoined.** `"pro -\nduces"` becomes `"produces"`. Only that exact pattern (a space, a hyphen and a line break) is joined, so real hyphens such as `"two- or three-level"` are kept.

- **Tables are removed by position, not by text.** Each "Matrix of Topics vs. Reference Material" table starts at its title and ends where the next chapter begins. Matching repeated text would miss rows, because pypdf puts each table cell on its own line and the reference codes differ between rows. These tables were creating duplicate section headings. The introduction's list of knowledge areas is removed the same way: it ends at the item whose number equals the chapter count.

- **Tables with real content and figures are kept, for now.** Tables that explain concepts hold useful text, and figure labels don't create false headings. The evaluation is the place to check whether either needs cleaning.

## Chunking

- **Chunks follow sections, not a fixed size.** Sections are natural units of meaning, and the chapter and section numbers give each chunk an ID and a clear citation.

- **Positions are used as cut points.** Chapter and section headings are put in one list sorted by position, and each chunk runs from its heading to the next heading of either kind, so no section runs into the next chapter. Chunk lengths never need to be computed.

- **The chapter is tracked across the loop.** Section numbers restart in every chapter, so each section takes the number of the last chapter heading seen, giving IDs such as `ch02-1.` and `ch05-1.`.

- **Long sections are split at 1,500 characters with 150 characters of overlap.** The overlap keeps an idea that crosses a cut in both parts. The size is a starting value, to be tuned with evaluation results.

- **The introduction is chunked by size.** Its numbered lists aren't sections, so it is split off before section detection and divided into parts (`intro-p1`, `intro-p2`). It turned out to answer basic questions such as "What is software engineering?".

- **Citations use section IDs, not page numbers.** Section numbers restart in each chapter, so a chapter-and-section ID is the reliable reference.

## Embedding

- **Batches of 25 chunks, one batch per minute.** Voyage's free tier allows 10,000 tokens per minute, and a batch of 25 chunks stays under that. A rate-limited batch waits 60 seconds and retries, up to 5 times, so a failure only retries that batch.

- **Embeddings are computed once and saved.** Embedding every chunk takes about 50 minutes on the free tier, so it never runs per question. Only the question is embedded at answer time.

- **Chunks use `input_type="document"` and questions use `"query"`.** Voyage tunes each vector for its role, so questions and the passages that answer them match better.

- **One model, set in one place.** `config.py` holds the Voyage client and model name, and both the embedder and the retriever import them. Vectors from different models can't be compared, so they must never drift apart.

- **`embeddings.json` is saved without indentation.** It holds over a million numbers. Indenting would put each number on its own line and make the file several times larger, and nobody reads it by eye.

- **The Voyage SDK replaced an earlier REST workaround.** The `voyageai` SDK was first blocked by Windows Smart App Control, so the project called the API through `requests`. With newer package versions the SDK runs, so the embedder uses it. The REST approach remains a fallback.

## Retrieval

- **Brute-force search over all chunks.** Every question is compared with all 1,157 chunk vectors. That is exact, and takes well under a second at this size. An approximate index (pgvector, FAISS) only pays off at hundreds of thousands of chunks.

- **Cosine similarity is written by hand** in plain Python, to show how retrieval works. NumPy would be faster if needed.

- **A JSON file instead of a vector database.** About a thousand chunks load in a second and can be compared one by one in milliseconds. A database becomes worthwhile when the app is deployed or the data grows.

## Answering

- **Rules go in a system instruction, material in the content.** The system instruction tells Gemini to use only the context, cite a passage ID after each point, reply with an exact fallback message when the context lacks the answer, and ignore any instructions inside the context. The content holds the ID-labelled chunks, then the question.

- **Low temperature (0.2)** keeps answers close to the source text.

- **All top 3 chunks are passed**, not only the best one. In testing, the best section sometimes ranked second by a tiny margin, and answers often combine two sections.

- **Two layers of fallback.** A score threshold (0.35) stops clearly off-topic questions before Gemini is called. If a weak chunk passes, Gemini's rule still returns the fallback. In tests, a direct question scored 0.67, a paraphrase 0.42 and an off-topic question 0.32.

- **A separate message for service errors**, so a failed API call isn't confused with "not in the guide".

- **Functions return, the app prints.** `retrieve` and `answer` return values, and only `app.py` prints. A future FastAPI endpoint can reuse both unchanged.

- **Stages are separate and mostly document-independent.** Splitting, embedding, retrieval and answering work for any document. The cleaning rules in chunker.py are SWEBOK-specific; moving them into per-document settings is planned.

## Evaluation

- **Retrieval is measured with chunk IDs, not answer text.** Gemini words answers differently each time, but whether the right section was retrieved can be checked exactly.

- **Labels are made independently of the retriever.** Candidates come from a keyword-overlap search (`find`), and the expected IDs are chosen by reading them. Copying the retriever's own output would make the test grade itself.

- **Several IDs can be correct.** A question counts as a hit if any expected ID is in the top 3, since an answer can span sections or parts.

- **Off-topic questions are part of the set**, to check that the threshold and the fallback work.

## Generated data isn't committed

`pages.json`, `chunks.json`, `embeddings.json` and the debug files contain the guide's text, so they stay out of the repository. Running the scripts rebuilds them.

# Known limitations

- **Numbered lists and years are sometimes detected as sections.** Lines like `1. Validate input.` or `1912. Then, in 2021…` match the section pattern, creating duplicate chunk IDs and splitting real sections. This causes the one retrieval miss in the evaluation.
- **Headings that wrap onto two lines are cut off** in citations, for example `2.4. Some Paradigms for Development Life`.
- **Some headings and texts include reference codes**, such as `[1-c22, 2-c8]`.
- **Parts are cut at fixed positions,** so a part can start or end mid-word.
- **Page footnotes can appear inside chunk text**, because pypdf places them inline.
- **Answers can drop qualifiers:** one answer turned "typically, but not always" into "typically".
- **The 0.35 threshold is based on a few tests.** One off-topic question in the evaluation passes it.
- **The question pause counts questions, not time,** so it can pause even when the per-minute limit has already reset.

Fixing the chunker issues means re-chunking and re-embedding, so those fixes will be batched together and checked with the evaluation.