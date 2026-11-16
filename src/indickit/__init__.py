"""indickit: a small toolkit and benchmark for Indian-language text."""
from .normalize import normalize, to_ascii_digits, to_native_digits
from .scripts import Detection, detect, graphemes, script_of
from .stats import count_tokens, register_tokenizer, stats, token_tax
from .translit import convert_script, from_latin, to_latin, transliterate

__version__ = "0.1.0"
__all__ = [
    "detect", "Detection", "graphemes", "script_of",
    "normalize", "to_ascii_digits", "to_native_digits",
    "transliterate", "convert_script", "to_latin", "from_latin",
    "stats", "count_tokens", "register_tokenizer", "token_tax",
]
