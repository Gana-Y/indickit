"""Run:  python examples/quickstart.py"""
from indickit import (
    detect, graphemes, normalize, stats, to_latin, to_native_digits, token_tax, transliterate,
)

# 1. which script / language is this?
d = detect("ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ?")
print(d.script, d.language, d.shares)

# 2. type Indian languages with an ASCII keyboard (ITRANS) ...
print(transliterate("namaste", "itrans", "kannada"))        # ನಮಸ್ತೇ
print(transliterate("namastE", "itrans", "kannada"))        # ನಮಸ್ತೆ  (E = short e, used in Dravidian languages)
print(transliterate("kRRipayaa", "itrans", "devanagari"))   # कृपया
# ... and convert between scripts
print(transliterate("ಕನ್ನಡ", "kannada", "devanagari"))     # कन्नड
print(to_latin("ಕನ್ನಡ"))                                    # kannaDa

# 3. clean text
print(normalize("೧೨೩ ಕನ್ನಡ\u200b  ಭಾಷೆ", digits="ascii"))      # 123 ಕನ್ನಡ ಭಾಷೆ
print(to_native_digits("2024", "kannada"))                  # ೨೦೨೪

# 4. count what a reader sees (aksharas), not code points
print(graphemes("ಕನ್ನಡ"), stats("ಕನ್ನಡ"))

# 5. the token tax, in bytes (no tokenizer needed)
for row in token_tax("bytes", ["hi", "kn", "ta"]):
    print(f"{row['language']:<8} {row['ratio_vs_english']:.2f}x")
