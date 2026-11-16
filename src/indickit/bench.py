"""A small, deterministic benchmark for how well a model handles Indian languages.

No judge model is used: every task is scored by a rule (character n-gram overlap, script check,
exact match) so results are cheap, reproducible and comparable across models.
"""
from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Sequence

from .corpus import LANGUAGES, PARALLEL, TRANSLIT_WORDS
from .metrics import chrf, digits_match, exact, script_fidelity
from .normalize import to_native_digits
from .translit import from_latin

KINDS = ["translate", "respond", "translit", "numerals", "script_id"]
KIND_LABELS = {
    "translate": "Translate EN→X",
    "respond": "Answer in X script",
    "translit": "Romanised→script",
    "numerals": "Native digits",
    "script_id": "Identify script",
}
INDIC = [c for c in LANGUAGES if c != "en"]
NUMBERS = [7, 2024, 1234567]
SCRIPT_NAMES = {
    "devanagari": "Devanagari", "bengali": "Bengali", "gurmukhi": "Gurmukhi", "gujarati": "Gujarati",
    "odia": "Odia", "tamil": "Tamil", "telugu": "Telugu", "kannada": "Kannada", "malayalam": "Malayalam",
}


@dataclass
class Task:
    id: str
    kind: str
    lang: str
    prompt: str
    reference: Optional[str]
    script: str = ""


def build_tasks(langs: Optional[Sequence[str]] = None, kinds: Optional[Sequence[str]] = None, limit_per_cell: Optional[int] = None) -> List[Task]:
    langs = [l for l in (langs or INDIC) if l in INDIC]
    kinds = list(kinds or KINDS)
    tasks: List[Task] = []
    for lang in langs:
        name, script = LANGUAGES[lang]
        if "translate" in kinds:
            for i, en in enumerate(PARALLEL["en"]):
                tasks.append(Task(
                    f"translate/{lang}/{i}", "translate", lang,
                    f"Translate the following English sentence into {name}. Reply with only the translation.\n\n{en}",
                    PARALLEL[lang][i], script))
        if "respond" in kinds:
            tasks.append(Task(
                f"respond/{lang}/0", "respond", lang,
                f"Write one short sentence about the weather today, in {name}. "
                f"Use only {name} script (no English, no transliteration). Reply with the sentence only.",
                None, script))
        if "translit" in kinds and script != "tamil":   # Tamil script cannot express ITRANS aspirates/voiced stops
            for i, w in enumerate(TRANSLIT_WORDS):
                tasks.append(Task(
                    f"translit/{lang}/{i}", "translit", lang,
                    f"The following word is written in ITRANS (ASCII romanisation). Write it in {name} script. "
                    f"Reply with only the converted word.\n\n{w}",
                    from_latin(w, script), script))
        if "numerals" in kinds:
            for i, n in enumerate(NUMBERS):
                tasks.append(Task(
                    f"numerals/{lang}/{i}", "numerals", lang,
                    f"Write the number {n} using {name} digits (not 0-9). Reply with only the digits, no commas.",
                    to_native_digits(str(n), script), script))
        if "script_id" in kinds:
            for i in (0, 3):
                tasks.append(Task(
                    f"script_id/{lang}/{i}", "script_id", lang,
                    "Which writing system (script) is this text written in? Answer with just the script name.\n\n"
                    + PARALLEL[lang][i],
                    SCRIPT_NAMES[script], script))
    if limit_per_cell:
        seen: Dict[tuple, int] = {}
        kept = []
        for t in tasks:
            key = (t.kind, t.lang)
            seen[key] = seen.get(key, 0) + 1
            if seen[key] <= limit_per_cell:
                kept.append(t)
        tasks = kept
    return tasks


def _clean(resp: str) -> str:
    resp = resp.strip()
    resp = re.sub(r"^```[a-z]*\n|\n```$", "", resp)
    return resp.strip().strip('"“”').strip()


def score(task: Task, response: str) -> Dict[str, float]:
    r = _clean(response)
    if task.kind == "translate":
        return {"score": chrf(r, task.reference or ""), "script": script_fidelity(r, task.script)}
    if task.kind == "respond":
        s = script_fidelity(r, task.script)
        return {"score": s, "script": s}
    if task.kind == "translit":
        return {"score": chrf(r, task.reference or ""), "exact": exact(r, task.reference or "")}
    if task.kind == "numerals":
        s = digits_match(r, task.reference or "")
        return {"score": s}
    if task.kind == "script_id":
        want = (task.reference or "").lower()
        return {"score": 1.0 if want in r.lower() else 0.0}
    raise ValueError(task.kind)


def run(provider, tasks: Sequence[Task], workers: int = 4, progress=None) -> dict:
    t0 = time.time()

    def one(task: Task) -> dict:
        try:
            resp, err = provider.complete(task.prompt, task), ""
        except Exception as exc:  # keep going; record the failure
            resp, err = "", f"{type(exc).__name__}: {exc}"
        sc = score(task, resp) if not err else {"score": 0.0}
        if progress:
            progress(task)
        return {**asdict(task), "response": resp, "error": err, **{f"m_{k}": v for k, v in sc.items()}, "score": sc["score"]}

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        results = list(pool.map(one, tasks))
    return {
        "meta": {"model": getattr(provider, "name", "unknown"), "tasks": len(tasks),
                 "seconds": round(time.time() - t0, 1), "version": 1},
        "results": results,
    }


def aggregate(data: dict) -> Dict[str, Dict[str, float]]:
    """{lang: {kind: mean_score, 'overall': mean}} (errors count as 0)."""
    cells: Dict[tuple, List[float]] = {}
    for r in data["results"]:
        cells.setdefault((r["lang"], r["kind"]), []).append(r["score"])
    table: Dict[str, Dict[str, float]] = {}
    for (lang, kind), v in cells.items():
        table.setdefault(lang, {})[kind] = sum(v) / len(v)
    for lang, row in table.items():
        row["overall"] = sum(row.values()) / len(row)
    return table


def save(data: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)


def load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)
