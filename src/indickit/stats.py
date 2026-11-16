"""Text statistics, including the 'token tax' view (how much longer is the same sentence?)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from .scripts import graphemes


@dataclass
class TextStats:
    chars: int          # Unicode code points
    graphemes: int      # akshara-level units
    words: int
    utf8_bytes: int
    utf16_units: int

    def as_dict(self) -> Dict[str, int]:
        return self.__dict__.copy()


def stats(text: str) -> TextStats:
    return TextStats(
        chars=len(text),
        graphemes=len(graphemes(text)),
        words=len(re.findall(r"\S+", text)),
        utf8_bytes=len(text.encode("utf-8")),
        utf16_units=len(text.encode("utf-16-le")) // 2,
    )


# ---------------------------------------------------------------------------
# Tokenizer registry: "bytes", "chars", "graphemes" are built in; others load lazily.
# ---------------------------------------------------------------------------
_REGISTRY: Dict[str, Callable[[str], int]] = {}


def register_tokenizer(name: str, count_fn: Callable[[str], int]) -> None:
    """Make ``name`` usable as a tokenizer spec: ``count_fn(text) -> number of tokens``."""
    _REGISTRY[name] = count_fn


def _load(spec: str) -> Callable[[str], int]:
    if spec in _REGISTRY:
        return _REGISTRY[spec]
    if spec == "bytes":
        return lambda t: len(t.encode("utf-8"))
    if spec == "chars":
        return len
    if spec == "graphemes":
        return lambda t: len(graphemes(t))
    kind, _, name = spec.partition(":")
    if kind == "tiktoken":
        try:
            import tiktoken
        except ImportError as exc:
            raise ImportError("pip install tiktoken   (or: pip install 'indickit[tokenizers]')") from exc
        enc = tiktoken.get_encoding(name or "o200k_base")
        return lambda t: len(enc.encode(t))
    if kind == "hf":
        try:
            from tokenizers import Tokenizer
        except ImportError as exc:
            raise ImportError("pip install tokenizers   (or: pip install 'indickit[tokenizers]')") from exc
        tok = Tokenizer.from_pretrained(name)
        return lambda t: len(tok.encode(t, add_special_tokens=False).ids)
    raise ValueError(
        f"unknown tokenizer {spec!r}. Use 'bytes', 'chars', 'graphemes', 'tiktoken:<encoding>', "
        "'hf:<repo-id>' or register_tokenizer(...)."
    )


def count_tokens(text: str, tokenizer: str = "bytes") -> int:
    return _load(tokenizer)(text)


def token_tax(tokenizer: str = "bytes", languages: Optional[List[str]] = None) -> List[dict]:
    """Average cost of the built-in parallel sentences per language, relative to English.

    ``tokenizer='bytes'`` is exact and needs nothing installed (UTF-8 bytes are the unit a byte-level
    BPE tokenizer starts from). Use ``tiktoken:o200k_base`` or ``hf:<repo>`` for real token counts.
    """
    from .corpus import LANGUAGES, PARALLEL

    fn = _load(tokenizer)
    en_total = sum(fn(s) for s in PARALLEL["en"])
    rows = []
    for code, (name, script) in LANGUAGES.items():
        if languages and code not in languages and code != "en":
            continue
        sents = PARALLEL[code]
        total = sum(fn(s) for s in sents)
        rows.append(
            {
                "code": code, "language": name, "script": script,
                "avg_cost": total / len(sents),
                "ratio_vs_english": total / en_total,
                "avg_graphemes": sum(len(graphemes(s)) for s in sents) / len(sents),
            }
        )
    return rows
