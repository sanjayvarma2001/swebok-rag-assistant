# Use it with your own PDF

The pipeline works with other documents, such as study notes, a textbook or a manual. The cleaning rules in `chunker.py` are tuned to the SWEBOK Guide, so adapting them to your PDF is the main work, and a good way to learn how RAG data preparation works.

## Before you start

Follow the setup in the [README](README.md#run-it-locally), so you can run the project on the SWEBOK Guide first. Seeing it work once makes it much easier to tell what changes for your document.

## Steps

### 1. Extract your PDF's text

Point `pdf_loader.py` at your file and run it. Open `pages.json` and look at a few pages: is the text readable, and in the right order? Scanned PDFs (images of pages) contain no text, so they need OCR first.

### 2. Set the page range

In `chunker.py`, set `FIRST_CONTENT_PAGE` and `LAST_CONTENT_PAGE` to skip the cover, table of contents, index and appendices. The table of contents is especially worth skipping: it lists every heading, so it matches many questions without answering any.

### 3. Check the page headers

`clean_pages` removes the first line of every page, because that's where SWEBOK's running header sits. Look at your pages: if your headers are on a different line, or there are none, change or remove this step.

### 4. Adapt the heading patterns

This is the most important step. Chunks follow your document's structure, so the patterns must find its headings.

- `CHAPTER_PATTERN` matches SWEBOK's `CHAPTER 02` followed by a title line.
- `SECTION_PATTERN` matches numbered headings such as `4.2. Unit Testing`.

Run `python chunker.py --debug`, open the files in `debug/`, and look at how your headings actually appear in the extracted text. Print them with `repr()` to see hidden spaces and line breaks. Then adjust the patterns.

If your document has no numbered sections, the simplest option is to skip section detection and chunk everything by size with `split_by_size`.

### 5. Remove or replace the SWEBOK-specific steps

`TABLE_MARKER`, `remove_tables`, `START_TABLE` and `remove_intro_table` target tables that only exist in the SWEBOK Guide. You probably don't need them. If your PDF has similar noise (repeated tables, long reference lists), use the same idea: find where it starts and ends, and cut by position.

### 6. Check the chunks before embedding

Embedding takes time on the free tier, so make sure the chunks are right first:

- **The count** is reasonable for your document.
- **A few chunks look right** when you read them: each starts at a heading and stops before the next one.
- **All chunk IDs are unique.** Duplicates mean something that isn't a heading matched your pattern.

### 7. Embed and try it

Run `python embedder.py`, then `python app.py`. Ask questions you know the answers to.

### 8. Measure it

Replace the questions in `eval.py` with your own: about 15 your document answers and 5 it doesn't. Label the expected chunk IDs by reading the chunks, not by copying what the retriever returns. Then run `python eval.py`, and use the misses to decide what to fix next.

## Tips

- **Look at the data at every step.** Most problems are visible in the `debug/` files long before they show up as bad answers.
- **Check with counts.** Before and after each cleaning step, compare text lengths and heading counts. A step that silently does nothing is the hardest bug to spot.
- **Change one thing at a time,** and re-run the evaluation to see whether it helped.

If you get it working on a new subject, I'd love to hear about it. Open an issue or a discussion and share what you changed.