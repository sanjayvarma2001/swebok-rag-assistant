# Software Engineer Assistant - Chat Bot

A chatbot that helps junior developers and students learn software engineering concepts. It answers questions using only the IEEE SWEBOK Guide (v4.0a), cites the chapter and section each answer comes from, and says when the guide doesn't cover a question instead of guessing.

It's built with retrieval-augmented generation (RAG), from scratch, without frameworks: the guide is split into sections and embedded once, and each question retrieves the most relevant sections before Gemini writes the answer.

> **Status:** working end to end, and evaluated on 22 hand-labelled questions (see [Evaluation](#evaluation)).

## How it works

**Indexing (runs once)**

1. **Load:** extract the text of each PDF page.
2. **Clean:** keep the content pages, remove page headers, normalise ligatures, rejoin hyphenated words, and remove reference tables.
3. **Chunk:** split the text by chapter and section, with IDs such as `ch04-4.2.`. Long sections are split into parts (`-p1`, `-p2`).
4. **Embed:** turn each chunk into a 1024-number vector with Voyage AI.

**Answering (every question)**

1. **Embed the question** with the same Voyage model.
2. **Retrieve:** score every chunk with cosine similarity and keep the top 3.
3. **Filter:** drop chunks scoring below 0.35. If none are left, return the fallback message without calling Gemini.
4. **Generate:** Gemini answers only from those chunks and cites a section ID for each point. If the chunks don't contain the answer, it returns the fallback message.

## Tech stack

| Purpose | Tool |
| --- | --- |
| Language | Python |
| PDF text extraction | pypdf |
| Embeddings | Voyage AI (`voyage-4`) |
| Answer generation | Google Gemini (`gemini-2.5-flash`, `google-genai`) |
| Storage | JSON files |
| Configuration | python-dotenv, shared `config.py` |

## Run it locally

### Requirements

- Python 3.12 or newer
- A free [Voyage AI](https://www.voyageai.com/) API key (embeddings)
- A free [Google Gemini](https://ai.google.dev/) API key (answers)

### 1. Clone and install

```bash
git clone https://github.com/sanjayvarma2001/swebok-rag-assistant.git
cd swebok-rag-assistant
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
```

### 2. Add your API keys

Create a `.env` file in the project root:

```
VOYAGE_API_KEY=your_voyage_key
GEMINI_API_KEY=your_gemini_key
```

`.env` is git-ignored. Never commit your keys.

### 3. Add the PDF

Download the SWEBOK Guide v4.0a from IEEE and save it as `docs/swebok.pdf`. The PDF and everything generated from it stay out of the repository.

### 4. Build the index (once)

```bash
python pdf_loader.py     # extract the text    → pages.json
python chunker.py        # clean and chunk     → data/software_engineering/chunks.json
python embedder.py       # embed every chunk   → data/software_engineering/embeddings.json
```

- Add `--debug` to `chunker.py` to save each cleaning step to `debug/` for inspection.
- On Voyage's free tier, `embedder.py` takes about 50 minutes (one batch of 25 chunks per minute). Keep the computer awake while it runs.

### 5. Ask questions

```bash
python app.py
```

Type a question to get a cited answer and its sources. Type `exit` to quit. On the free tier, the app pauses for a minute after every 3 questions.

### 6. Run the evaluation

```bash
python eval.py
```

## Evaluation

22 questions, run with `python eval.py`: 17 the guide covers and 5 it doesn't.

| Check | Result |
| --- | --- |
| Correct section in the top 3 (answerable questions) | **16 / 17** |
| Off-topic questions rejected by the score threshold | **4 / 5** |

- **The one retrieval miss** (ethics) traces to a chunker bug: a year ("1912.") was detected as a section heading and split the codes-of-ethics section. Tracked in issue #[number].
- **The one off-topic question that passed the threshold** ("latest version of Python") is left to Gemini's fallback rule. Tracked in issue #[number].

Expected sections were labelled by hand, using keyword search to find candidates, independently of the retriever, so the evaluation doesn't grade itself.

## Roadmap

### Done
- [x] PDF loading, cleaning and section-based chunking
- [x] Embeddings (batched for the free tier)
- [x] Retrieval with cosine similarity
- [x] Grounded answers with section citations and a fallback
- [x] Question loop (`app.py`)
- [x] Evaluation on 22 labelled questions

### Later
- [ ] Fix false section headings from numbered lists and years
- [ ] Cut long sections at sentence ends; strip reference codes from headings
- [ ] Unit tests and CI
- [ ] Streaming answers and faster retrieval (NumPy)
- [ ] Hybrid search (keyword + vector)
- [ ] Web interface, FastAPI endpoint and pgvector

## More

- [Design decisions and known limitations](DESIGN.md)
- [Use it with your own PDF](ADAPTING.md)
- [Contributing](CONTRIBUTING.md)

## Source and copyright

This project answers questions from the *Guide to the Software Engineering Body of Knowledge
(SWEBOK Guide), Version 4.0a*, H. Washizaki, Ed., IEEE Computer Society, 2024.

- The SWEBOK Guide is © IEEE. It is **not included** in this repository. Download it yourself from
  the [IEEE Computer Society](https://www.computer.org/swebok).
- IEEE permits personal and educational use without fee, under the conditions in the guide's
  copyright notice. Commercial use, or redistributing its content, requires permission from IEEE.
- This project is not affiliated with or endorsed by IEEE.
- The MIT licence below covers **this project's code only**, not the SWEBOK Guide or any
  document you use with it.

## Licence

[MIT](LICENSE). The SWEBOK Guide itself is © IEEE and is not included in this repository.