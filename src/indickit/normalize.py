"""Text normalisation for Indic text."""
from __future__ import annotations

import re
import unicodedata
from typing import Optional

from .scripts import BLOCKS

# first digit of each script's decimal digits
DIGIT_START = {
    "devanagari": 0x0966, "bengali": 0x09E6, "gurmukhi": 0x0A66, "gujarati": 0x0AE6, "odia": 0x0B66,
    "tamil": 0x0BE6, "telugu": 0x0C66, "kannada": 0x0CE6, "malayalam": 0x0D66,
}
_ZERO_WIDTH_ALWAYS = "\u200b\u2060\ufeff"   # ZWSP, word joiner, BOM: never meaningful in running text
_JOINERS = "\u200c\u200d"                   # ZWNJ / ZWJ: sometimes meaningful (conjuncts, chillu)


def to_ascii_digits(text: str) -> str:
    """'೧೨೩' -> '123' (all Indic digit systems)."""
    out = []
    for ch in text:
        for start in DIGIT_START.values():
            if start <= ord(ch) < start + 10:
                ch = chr(ord("0") + ord(ch) - start)
                break
        out.append(ch)
    return "".join(out)


def to_native_digits(text: str, script: str) -> str:
    """'123' -> '೧೨೩' for ``script='kannada'``. Converts ASCII and other Indic digits."""
    script = script.lower()
    if script not in DIGIT_START:
        raise ValueError(f"unknown script {script!r}; choose from {sorted(DIGIT_START)}")
    start = DIGIT_START[script]
    return "".join(chr(start + int(c)) if c.isdigit() and c.isascii() else c for c in to_ascii_digits(text))


def normalize(
    text: str,
    *,
    digits: Optional[str] = None,
    keep_joiners: bool = True,
    danda: bool = False,
    collapse_whitespace: bool = True,
) -> str:
    """Normalise Indic text.

    * Unicode NFC, removal of zero-width space / BOM / word-joiner characters.
    * ``keep_joiners=False`` also drops ZWJ/ZWNJ (useful for search/matching; can change rendering).
    * ``digits='ascii'`` converts all Indic digits to 0-9; ``digits='kannada'`` (or any script) to native digits.
    * ``danda=True`` turns the danda '।' and '॥' into '.'.
    * Collapses runs of whitespace.
    """
    text = unicodedata.normalize("NFC", text)
    text = re.sub(f"[{_ZERO_WIDTH_ALWAYS}]", "", text)
    if not keep_joiners:
        text = re.sub(f"[{_JOINERS}]", "", text)
    if digits:
        text = to_ascii_digits(text) if digits == "ascii" else to_native_digits(text, digits)
    if danda:
        text = text.replace("॥", ".").replace("।", ".")
    if collapse_whitespace:
        text = re.sub(r"[ \t\u00a0]+", " ", text)
        text = re.sub(r"\s*\n\s*", "\n", text).strip()
    return text
