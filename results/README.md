# Community benchmark results

Run the benchmark on a model and share the numbers:

```bash
indickit bench run --provider ollama --model llama3.2 -o results/llama3.2.json
indickit bench report results/llama3.2.json --svg results/llama3.2.svg
```

Then open a PR adding both files (the JSON contains every prompt, response and score, so anyone can audit it).
Please include in the PR description: model name and version, provider, date, and whether you changed any settings.

No results are published here yet. The first ones are yours to add.
