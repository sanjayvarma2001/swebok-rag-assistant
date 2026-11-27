# Contributing

Thanks for your interest. Bug reports, ideas and pull requests are all welcome. This is a learning project, so questions are welcome too.

## Reporting a bug

[Open an issue](../../issues/new) and include:

- **What you did:** the question you asked, or the command you ran
- **What you expected** to happen
- **What happened instead:** the answer, the error message or the output
- **Your setup:** operating system and Python version

For a wrong or missing answer, also include the sources (chunk IDs and scores) that `app.py` printed. They show whether the problem is in retrieval or in the answer.

Never paste your API keys into an issue.

## Suggesting an improvement

Check the [open issues](../../issues) and the Roadmap in the [README](README.md#roadmap) first, in case it's already planned. If not, open an issue describing the idea and why it would help.

## Good places to start

Issues labelled `good first issue` are small and self-contained. Some areas that need work:

- fixing false section headings in the chunker (numbered lists and years)
- cutting long sections at sentence ends instead of fixed positions
- unit tests for the pure functions (`split_by_size`, `build_chunks`, `cosine`)
- a web chat interface

## Making a change

1. **Fork the repository** and clone your fork.
2. **Set up the project** by following [Run it locally](README.md#run-it-locally).
3. **Create a branch** for your change:
   ```bash
   git switch -c fix/short-description
   ```
4. **Keep the change focused:** one fix or feature per pull request.
5. **Test it:**
   - Run `python app.py` and ask a few questions.
   - If your change affects chunking, embedding or retrieval, run `python eval.py` before and after, and include both results in the pull request.
6. **Open a pull request** describing what changed, why, and how you tested it. If it fixes an issue, write `Fixes #<issue number>` so the issue closes automatically when it's merged.

## Code style

- Follow the existing style: snake_case names, UPPER_SNAKE constants at the top of the file, and a short docstring for each function.
- Keep each function to one job, and keep settings in `config.py`.
- Don't commit generated data (`data/`, `debug/`, `pages.json`), the PDF, or `.env`.

## Questions

If something in the code or the design isn't clear, open an issue and ask. The [design decisions](DESIGN.md) explain why things are built the way they are.