"""Command line interface."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from . import __version__
from .normalize import normalize
from .scripts import detect, graphemes
from .stats import stats, token_tax
from .translit import transliterate


def _text(args) -> str:
    if args.text:
        return " ".join(args.text)
    if not sys.stdin.isatty():
        return sys.stdin.read().rstrip("\n")
    raise SystemExit("error: provide TEXT or pipe text on stdin")


def cmd_detect(args) -> int:
    d = detect(_text(args))
    if args.json:
        print(json.dumps(d.__dict__, ensure_ascii=False, indent=2))
        return 0
    print(f"script   : {d.script}")
    print(f"language : {d.language}   (candidates: {', '.join(d.candidates) or '-'})")
    print("shares   : " + ", ".join(f"{k} {v:.0%}" for k, v in d.shares.items()))
    if d.mixed:
        print("note     : code-mixed (Latin + Indic script)")
    if d.romanized:
        print("note     : looks like romanised Hindi (Hinglish)")
    return 0


def cmd_translit(args) -> int:
    text = _text(args)
    print(transliterate(text, args.source, args.to))
    return 0


def cmd_normalize(args) -> int:
    print(normalize(_text(args), digits=args.digits, keep_joiners=not args.drop_joiners, danda=args.danda))
    return 0


def cmd_stats(args) -> int:
    text = _text(args)
    s = stats(text)
    print(f"characters (code points): {s.chars}")
    print(f"graphemes (aksharas)    : {s.graphemes}")
    print(f"words                   : {s.words}")
    print(f"UTF-8 bytes             : {s.utf8_bytes}")
    print(f"UTF-16 units            : {s.utf16_units}")
    print("graphemes: " + " ".join(graphemes(text)[:40]))
    return 0


def cmd_tax(args) -> int:
    rows = token_tax(args.tokenizer, args.langs.split(",") if args.langs else None)
    unit = args.tokenizer
    print(f"Cost of the same 6 sentences, unit = {unit}   (English = 1.00x)\n")
    print(f"{'Language':<11}{'Script':<12}{'avg/sentence':>13}{'vs English':>12}")
    for r in sorted(rows, key=lambda r: r["ratio_vs_english"]):
        bar = "█" * int(round(r["ratio_vs_english"] * 6))
        print(f"{r['language']:<11}{r['script']:<12}{r['avg_cost']:>13.1f}{r['ratio_vs_english']:>11.2f}x  {bar}")
    return 0


def cmd_bench_run(args) -> int:
    from . import bench
    from .llm import make_provider
    from .report import to_markdown

    provider = make_provider(args.provider, args.model, args.base_url)
    tasks = bench.build_tasks(args.langs.split(",") if args.langs else None,
                              args.kinds.split(",") if args.kinds else None, args.limit)
    print(f"running {len(tasks)} tasks against {provider.name} ...", file=sys.stderr)
    done = [0]

    def progress(_t):
        done[0] += 1
        if done[0] % 20 == 0:
            print(f"  {done[0]}/{len(tasks)}", file=sys.stderr)

    data = bench.run(provider, tasks, workers=args.workers, progress=progress)
    bench.save(data, args.output)
    print(to_markdown(data))
    print(f"\nsaved {args.output}", file=sys.stderr)
    return 0


def cmd_bench_report(args) -> int:
    from . import bench
    from .report import to_markdown, to_svg

    data = bench.load(args.results)
    if args.svg:
        with open(args.svg, "w", encoding="utf-8") as fh:
            fh.write(to_svg(data))
        print(f"wrote {args.svg}", file=sys.stderr)
    print(to_markdown(data))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="indickit", description="Toolkit and benchmark for Indian-language text.")
    p.add_argument("--version", action="version", version=f"indickit {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("detect", help="detect script and likely language")
    s.add_argument("text", nargs="*"); s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_detect)

    s = sub.add_parser("translit", help="transliterate between scripts / ITRANS")
    s.add_argument("text", nargs="*")
    s.add_argument("--from", dest="source", default="itrans", help="itrans (default) or a script name")
    s.add_argument("--to", required=True, help="kannada, devanagari, tamil, ... or itrans")
    s.set_defaults(fn=cmd_translit)

    s = sub.add_parser("normalize", help="clean up Indic text")
    s.add_argument("text", nargs="*")
    s.add_argument("--digits", help="'ascii' or a script name (kannada, devanagari, ...)")
    s.add_argument("--drop-joiners", action="store_true"); s.add_argument("--danda", action="store_true")
    s.set_defaults(fn=cmd_normalize)

    s = sub.add_parser("stats", help="characters, graphemes, bytes")
    s.add_argument("text", nargs="*"); s.set_defaults(fn=cmd_stats)

    s = sub.add_parser("tax", help="the 'token tax': cost of the same sentences across languages")
    s.add_argument("--tokenizer", default="bytes", help="bytes (default), graphemes, tiktoken:o200k_base, hf:<repo-id>")
    s.add_argument("--langs", help="comma-separated codes, e.g. hi,kn,ta")
    s.set_defaults(fn=cmd_tax)

    b = sub.add_parser("bench", help="benchmark a model on Indian languages").add_subparsers(dest="bcmd", required=True)
    r = b.add_parser("run", help="run the benchmark")
    r.add_argument("--provider", required=True, help="openai | anthropic | groq | openrouter | gemini | ollama | mock-oracle | mock-echo")
    r.add_argument("--model"); r.add_argument("--base-url")
    r.add_argument("--langs", help="e.g. hi,kn,ta"); r.add_argument("--kinds", help="translate,respond,translit,numerals,script_id")
    r.add_argument("--limit", type=int, help="max tasks per (kind, language) cell")
    r.add_argument("--workers", type=int, default=4); r.add_argument("-o", "--output", default="results.json")
    r.set_defaults(fn=cmd_bench_run)
    q = b.add_parser("report", help="Markdown / SVG report from a results file")
    q.add_argument("results"); q.add_argument("--svg"); q.set_defaults(fn=cmd_bench_report)

    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except (ValueError, ImportError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
