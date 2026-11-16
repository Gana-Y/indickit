"""Pure-Python metrics that work for any script."""
from __future__ import annotations

import re
from collections import Counter
from typing import Optional

from .normalize import to_ascii_digits
from .scripts import BLOCKS, script_of


def _ngrams(s: str, n: int) -> Counter:
    return Counter(s[i : i + n] for i in range(len(s) - n + 1))


def chrf(hypothesis: str, reference: str, n: int = 6, beta: float = 2.0) -> float:
    """Character n-gram F-score (chrF, Popovic 2015), 0..1. Whitespace is ignored.

    Works well for morphologically rich, agglutinative languages where word-level BLEU is harsh.
    """
    hyp = re.sub(r"\s+", "", hypothesis)
    ref = re.sub(r"\s+", "", reference)
    if not hyp or not ref:
        return 1.0 if hyp == ref else 0.0
    precisions, recalls = [], []
    for k in range(1, n + 1):
        h, r = _ngrams(hyp, k), _ngrams(ref, k)
        if not h or not r:
            continue
        overlap = sum((h & r).values())
        precisions.append(overlap / sum(h.values()))
        recalls.append(overlap / sum(r.values()))
    if not precisions:
        return 0.0
    p, r = sum(precisions) / len(precisions), sum(recalls) / len(recalls)
    if p + r == 0:
        return 0.0
    b2 = beta * beta
    return (1 + b2) * p * r / (b2 * p + r)


def script_fidelity(text: str, script: str) -> float:
    """Share of letters in ``text`` that belong to ``script`` (0..1)."""
    script = script.lower()
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(script_of(c) == script for c in letters) / len(letters)


def exact(hypothesis: str, reference: str) -> float:
    norm = lambda s: re.sub(r"[\s\.,;:!?\"'।॥]+", "", s)  # noqa: E731
    return 1.0 if norm(hypothesis) == norm(reference) else 0.0


def digits_match(hypothesis: str, reference: str) -> float:
    """1.0 if the response contains exactly the reference digits (native or ASCII), else 0.0."""
    got = re.sub(r"[\s,\.]", "", hypothesis)
    return 1.0 if got == reference else 0.0
