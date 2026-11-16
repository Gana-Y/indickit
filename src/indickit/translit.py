"""Transliteration.

* Brahmic script <-> Brahmic script by Unicode block offset (the nine scripts share one layout).
* Latin (ITRANS-style ASCII) <-> any Brahmic script, via a Devanagari pivot.

Transliteration is *sound-for-sound script conversion*, not translation. Limits are documented in README.
"""
from __future__ import annotations

import unicodedata
from typing import Dict, List, Optional, Tuple

from .scripts import BLOCKS, VIRAMAS

# Devanagari offsets (0..0x7F) that Tamil cannot express, mapped to the closest Tamil letter.
_TAMIL_FALLBACK = {
    0x16: 0x15, 0x17: 0x15, 0x18: 0x15,     # kha ga gha  -> ka
    0x1B: 0x1A, 0x1D: 0x1C,                 # cha jha     -> ca ja
    0x20: 0x1F, 0x21: 0x1F, 0x22: 0x1F,     # ttha dda ddha -> tta
    0x25: 0x24, 0x26: 0x24, 0x27: 0x24,     # tha da dha  -> ta
    0x2B: 0x2A, 0x2C: 0x2A, 0x2D: 0x2A,     # pha ba bha  -> pa
}


def _block(ch: str) -> Optional[str]:
    base = ord(ch) & ~0x7F
    for name, start in BLOCKS.items():
        if start == base:
            return name
    return None


def convert_script(text: str, target: str) -> str:
    """Convert Brahmic-script characters in ``text`` to ``target`` script.

    >>> convert_script("ಕನ್ನಡ", "devanagari")
    'कन्नड'

    Characters outside the nine Brahmic blocks (Latin, digits, punctuation) are kept.
    Converting *to* Tamil is lossy (Tamil has no separate aspirated/voiced letters);
    code points the target script does not have are left unchanged.
    """
    target = target.lower()
    if target not in BLOCKS:
        raise ValueError(f"unknown script {target!r}; choose from {sorted(BLOCKS)}")
    tstart = BLOCKS[target]
    out: List[str] = []
    for ch in unicodedata.normalize("NFC", text):
        src = _block(ch)
        if src is None or src == target:
            out.append(ch)
            continue
        off = ord(ch) - BLOCKS[src]
        if target == "tamil" and off in _TAMIL_FALLBACK:
            off = _TAMIL_FALLBACK[off]
        new = chr(tstart + off)
        out.append(new if unicodedata.category(new) != "Cn" else ch)
    return "".join(out)


# ---------------------------------------------------------------------------
# ITRANS-style Latin <-> Devanagari
# ---------------------------------------------------------------------------
VIRAMA = "\u094d"
# independent vowel, matra
_VOWELS: Dict[str, Tuple[str, str]] = {
    "a": ("अ", ""), "aa": ("आ", "ा"), "A": ("आ", "ा"),
    "i": ("इ", "ि"), "ii": ("ई", "ी"), "I": ("ई", "ी"), "ee": ("ई", "ी"),
    "u": ("उ", "ु"), "uu": ("ऊ", "ू"), "U": ("ऊ", "ू"), "oo": ("ऊ", "ू"),
    "RRi": ("ऋ", "ृ"), "RRI": ("ॠ", "ॄ"), "LLi": ("ऌ", "ॢ"),
    "e": ("ए", "े"), "ai": ("ऐ", "ै"), "o": ("ओ", "ो"), "au": ("औ", "ौ"),
    "E": ("ऎ", "ॆ"), "O": ("ऒ", "ॊ"),   # short e / o, needed for Dravidian languages
}
_MARKS = {"M": "ं", "H": "ः", ".N": "ँ", ".a": "ऽ", "||": "॥", "|": "।"}
_CONS = {
    "k": "क", "kh": "ख", "g": "ग", "gh": "घ", "~N": "ङ", "N^": "ङ",
    "ch": "च", "Ch": "छ", "j": "ज", "jh": "झ", "~n": "ञ",
    "T": "ट", "Th": "ठ", "D": "ड", "Dh": "ढ", "N": "ण",
    "t": "त", "th": "थ", "d": "द", "dh": "ध", "n": "न",
    "p": "प", "ph": "फ", "b": "ब", "bh": "भ", "m": "म",
    "y": "य", "r": "र", "l": "ल", "v": "व", "w": "व",
    "sh": "श", "Sh": "ष", "s": "स", "h": "ह", "L": "ळ",
    "x": "क्ष", "GY": "ज्ञ",
}
_LATIN_TOKENS = sorted(set(_VOWELS) | set(_MARKS) | set(_CONS), key=len, reverse=True)

# canonical spellings when going Devanagari -> Latin
_DEV_VOWEL_LATIN = {
    "अ": "a", "आ": "aa", "इ": "i", "ई": "ii", "उ": "u", "ऊ": "uu", "ऋ": "RRi", "ॠ": "RRI", "ऌ": "LLi",
    "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au", "ऎ": "E", "ऒ": "O",
}
_DEV_MATRA_LATIN = {
    "ा": "aa", "ि": "i", "ी": "ii", "ु": "u", "ू": "uu", "ृ": "RRi", "ॄ": "RRI", "ॢ": "LLi",
    "े": "e", "ै": "ai", "ो": "o", "ौ": "au", "ॆ": "E", "ॊ": "O",
}
_DEV_CONS_LATIN = {
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "~N", "च": "ch", "छ": "Ch", "ज": "j", "झ": "jh", "ञ": "~n",
    "ट": "T", "ठ": "Th", "ड": "D", "ढ": "Dh", "ण": "N", "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m", "य": "y", "र": "r", "ल": "l", "व": "v",
    "श": "sh", "ष": "Sh", "स": "s", "ह": "h", "ळ": "L",
    "ऴ": "zh", "ऱ": "rr", "ऩ": "nn",       # Tamil/Malayalam/Dravidian letters (one-way)
}
_DEV_MARK_LATIN = {"ं": "M", "ः": "H", "ँ": ".N", "ऽ": ".a", "।": "|", "॥": "||"}
_NUKTA = "़"


def latin_to_devanagari(text: str) -> str:
    """ITRANS-style ASCII -> Devanagari.

    A consonant directly followed by another consonant gets a virama (``namaste`` -> नमस्ते,
    ``kSha`` -> क्ष); a consonant at the end of a word keeps its inherent vowel (``raam`` -> राम).
    """
    out: List[str] = []
    after_cons = False
    i = 0
    while i < len(text):
        for tok in _LATIN_TOKENS:
            if text.startswith(tok, i):
                break
        else:
            tok = None
        if tok is None:
            out.append(text[i])
            after_cons = False
            i += 1
            continue
        i += len(tok)
        if tok in _CONS:
            if after_cons:
                out.append(VIRAMA)
            out.append(_CONS[tok])
            after_cons = True
        elif tok in _VOWELS:
            indep, matra = _VOWELS[tok]
            out.append(matra if after_cons else indep)
            after_cons = False
        else:
            out.append(_MARKS[tok])
            after_cons = False
    return "".join(out)


def devanagari_to_latin(text: str) -> str:
    """Devanagari -> ITRANS-style ASCII (strict: inherent 'a' is always written)."""
    text = unicodedata.normalize("NFC", text)
    out: List[str] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch in _DEV_CONS_LATIN:
            out.append(_DEV_CONS_LATIN[ch])
            i += 1
            while i < n and text[i] == _NUKTA:
                i += 1
            nxt = text[i] if i < n else ""
            if nxt == VIRAMA:
                i += 1
            elif nxt in _DEV_MATRA_LATIN:
                out.append(_DEV_MATRA_LATIN[nxt])
                i += 1
            else:
                out.append("a")
            continue
        if ch in _DEV_VOWEL_LATIN:
            out.append(_DEV_VOWEL_LATIN[ch])
        elif ch in _DEV_MARK_LATIN:
            out.append(_DEV_MARK_LATIN[ch])
        elif ch in ("\u200c", "\u200d"):
            pass
        else:
            out.append(ch)
        i += 1
    return "".join(out)


# ---------------------------------------------------------------------------
def transliterate(text: str, source: str, target: str) -> str:
    """Transliterate between ``'itrans'`` (Latin) and any of the nine Brahmic scripts, or script to script.

    >>> transliterate("namaste", "itrans", "kannada")
    'ನಮಸ್ತೇ'
    >>> transliterate("ನಮಸ್ತೇ", "kannada", "itrans")
    'namaste'
    """
    source, target = source.lower(), target.lower()
    valid = set(BLOCKS) | {"itrans"}
    for name in (source, target):
        if name not in valid:
            raise ValueError(f"unknown scheme {name!r}; choose from {sorted(valid)}")
    if source == target:
        return text
    if source == "itrans":
        dev = latin_to_devanagari(text)
        return dev if target == "devanagari" else convert_script(dev, target)
    dev = text if source == "devanagari" else convert_script(text, "devanagari")
    if target == "itrans":
        return devanagari_to_latin(dev)
    return dev if target == "devanagari" else convert_script(dev, target)


def to_latin(text: str) -> str:
    """Any Brahmic script -> ITRANS-style Latin (mixed text is handled per character)."""
    return devanagari_to_latin(convert_script(text, "devanagari"))


def from_latin(text: str, script: str) -> str:
    return transliterate(text, "itrans", script)
