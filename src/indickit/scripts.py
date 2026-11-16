"""Script and language detection, plus grapheme (akshara) segmentation for Brahmic scripts."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# name -> (first code point of the 128-code-point Unicode block)
BLOCKS: Dict[str, int] = {
    "devanagari": 0x0900,
    "bengali": 0x0980,
    "gurmukhi": 0x0A00,
    "gujarati": 0x0A80,
    "odia": 0x0B00,
    "tamil": 0x0B80,
    "telugu": 0x0C00,
    "kannada": 0x0C80,
    "malayalam": 0x0D00,
}
SCRIPTS = list(BLOCKS)

VIRAMAS = {0x094D, 0x09CD, 0x0A4D, 0x0ACD, 0x0B4D, 0x0BCD, 0x0C4D, 0x0CCD, 0x0D4D}

# script -> languages that are written in it (ISO 639-1 where it exists)
SCRIPT_LANGS: Dict[str, List[str]] = {
    "devanagari": ["hi", "mr", "ne"],
    "bengali": ["bn", "as"],
    "gurmukhi": ["pa"],
    "gujarati": ["gu"],
    "odia": ["or"],
    "tamil": ["ta"],
    "telugu": ["te"],
    "kannada": ["kn"],
    "malayalam": ["ml"],
}

# Small stop-word lists to separate Devanagari languages. Heuristic: short texts are ambiguous.
_STOP = {
    "hi": "है हैं का की के में और को से पर यह था थी हूँ नहीं कि ने एक कैसे आप मैं हम तुम वह यहाँ कहाँ बहुत".split(),
    "mr": "आहे आहेत चा ची चे मध्ये आणि ला ना हे होते मी तुम्ही नाही काय कसे कुठे खूप आम्ही तो ती".split(),
    "ne": "छ हो को मा र लाई हुन्छ गर्न यो त्यो छन् म तिमी हामी कहाँ धेरै".split(),
    "bn": "আমি তুমি আপনি এবং কি কী না আছে হয় এই সেই জন্য থেকে করে খুব".split(),
    "as": "মই তুমি আৰু নহয় আছে হয় এই সেই বাবে পৰা কৰে ভাল".split(),
}
_HINGLISH = set(
    "hai hain nahi nahin kya aap mein main hum tum kaise kaisa bahut accha achha acha kar karo karna raha rahi "
    "ka ki ke ko se par yeh woh kab kahan kyun mujhe tumhe humein bhai yaar abhi thoda zyada kuch sab".split()
)


def script_of(ch: str) -> Optional[str]:
    """Script name of a single character, 'latin', 'digit'-agnostic, or None."""
    cp = ord(ch)
    base = cp & ~0x7F
    for name, start in BLOCKS.items():
        if start == base:
            return name
    if ch.isalpha() and cp < 0x250:
        return "latin"
    return None


@dataclass
class Detection:
    script: Optional[str]                     # dominant script ('kannada', 'latin', ...) or None
    shares: Dict[str, float] = field(default_factory=dict)   # script -> share of letters
    language: Optional[str] = None            # best guess ('kn', 'hi', 'hi-Latn' for romanised Hindi ...)
    candidates: List[str] = field(default_factory=list)
    mixed: bool = False                       # Latin and an Indic script both substantial (code-mixing)
    romanized: bool = False                   # Latin text that looks like romanised Hindi ("Hinglish")


def _words(text: str) -> List[str]:
    return re.findall(r"[\w\u0900-\u0DFF]+", text, flags=re.UNICODE)


def detect(text: str) -> Detection:
    """Detect the script(s) and most likely language of ``text``.

    The *script* result is reliable. The *language* result is exact for scripts used by a single
    language here, and a heuristic (stop-words) for Devanagari and Bengali-script text.
    """
    counts: Dict[str, int] = {}
    for ch in text:
        if not (ch.isalpha() or unicodedata.category(ch).startswith("M")):
            continue
        s = script_of(ch)
        if s:
            counts[s] = counts.get(s, 0) + 1
    total = sum(counts.values())
    if not total:
        return Detection(None)
    shares = {k: v / total for k, v in sorted(counts.items(), key=lambda kv: -kv[1])}
    top = next(iter(shares))
    indic = {k: v for k, v in shares.items() if k != "latin"}
    mixed = "latin" in shares and shares["latin"] >= 0.15 and bool(indic) and sum(indic.values()) >= 0.15
    det = Detection(script=top, shares=shares, mixed=mixed)

    if top == "latin":
        words = [w.lower() for w in _words(text)]
        hits = sum(w in _HINGLISH for w in words)
        if words and hits >= 2 and hits / len(words) >= 0.25:
            det.romanized, det.language, det.candidates = True, "hi-Latn", ["hi-Latn"]
        return det

    candidates = SCRIPT_LANGS.get(top, [])
    if len(candidates) == 1:
        det.language, det.candidates = candidates[0], list(candidates)
        return det
    words = set(_words(text))
    scored = sorted(((sum(w in words for w in _STOP.get(lang, [])), lang) for lang in candidates), reverse=True)
    det.candidates = [lang for _, lang in scored]
    det.language = scored[0][1] if scored and scored[0][0] > 0 else candidates[0]
    return det


# ---------------------------------------------------------------------------
# graphemes
# ---------------------------------------------------------------------------
def graphemes(text: str) -> List[str]:
    """Split into orthographic units (aksharas): consonant clusters joined by virama, with their vowel signs.

    ``"ಕನ್ನಡ"`` -> ``["ಕ", "ನ್ನ", "ಡ"]``.  Non-Brahmic text is split per code point (plus combining marks).
    """
    out: List[str] = []
    join_next = False
    for ch in text:
        cp = ord(ch)
        is_mark = unicodedata.category(ch).startswith("M") or cp in (0x200C, 0x200D)
        if out and (is_mark or join_next):
            out[-1] += ch
        else:
            out.append(ch)
        join_next = cp in VIRAMAS
    return out
