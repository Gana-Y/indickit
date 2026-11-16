# Contributing to indickit

Thanks for helping! Small PRs are the best PRs.

## Dev setup

```bash
git clone https://github.com/Gana-Y/indickit.git
cd indickit
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Guidelines

- Add or update tests for every behaviour change.
- Keep the public API small and the docs honest: if something is a heuristic, say so.
- Open an issue first for big changes so we can agree on the approach.

## Easiest ways to help

1. **Review the parallel sentences** in `src/indickit/corpus.py`. They were drafted with AI assistance and have
   *not* been verified by native speakers. If a sentence is wrong or unnatural, open a PR with the fix and say which
   language you speak. This is the most valuable contribution right now.
2. **Add a language** (Assamese, Nepali, Sanskrit, Konkani, Maithili ...). Add it to `LANGUAGES` / `PARALLEL` with
   the same 6 sentences, and run `pytest`: the corpus tests check the script of every sentence.
3. **Submit benchmark results** for a model: see `results/README.md`.
4. **Report transliteration bugs** with the input, the output you got and the output you expected.

By contributing you agree that your contribution is released under the MIT License.
