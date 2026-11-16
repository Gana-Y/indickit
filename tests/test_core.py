import pytest

from indickit import (
    convert_script, count_tokens, detect, from_latin, graphemes, normalize, register_tokenizer,
    stats, to_ascii_digits, to_latin, to_native_digits, token_tax, transliterate,
)
from indickit.corpus import LANGUAGES, PARALLEL
from indickit.scripts import script_of


# ---- detection -----------------------------------------------------------
@pytest.mark.parametrize("code", [c for c in LANGUAGES if c not in ("en", "hi", "mr")])
def test_unique_script_languages_are_detected_exactly(code):
    for sentence in PARALLEL[code]:
        d = detect(sentence)
        assert d.script == LANGUAGES[code][1]
        assert d.language == code


def test_devanagari_hindi_vs_marathi_on_corpus():
    # heuristic: assert the right language is the top guess for full-length sentences
    for code in ("hi", "mr"):
        text = " ".join(PARALLEL[code])
        assert detect(text).language == code


def test_english_and_empty_and_digits():
    d = detect("Hello world")
    assert d.script == "latin" and d.language is None and not d.mixed
    assert detect("").script is None
    assert detect("12345 !!!").script is None


def test_code_mixed_and_romanised_hindi():
    assert detect("Hello ನಮಸ್ಕಾರ friend ಹೇಗಿದ್ದೀರಿ").mixed
    h = detect("Aap kaise hain? Mujhe bahut accha laga")
    assert h.romanized and h.language == "hi-Latn"
    assert not detect("The weather is nice today").romanized


def test_detection_shares_sum_to_one():
    d = detect("ನಮಸ್ಕಾರ hello")
    assert sum(d.shares.values()) == pytest.approx(1.0)


def test_script_of():
    assert script_of("ಕ") == "kannada" and script_of("क") == "devanagari" and script_of("a") == "latin"
    assert script_of("1") is None and script_of(" ") is None


# ---- graphemes -----------------------------------------------------------
def test_graphemes():
    assert graphemes("ಕನ್ನಡ") == ["ಕ", "ನ್ನ", "ಡ"]
    assert graphemes("क्षत्रिय") == ["क्ष", "त्रि", "य"]
    assert graphemes("नमस्ते") == ["न", "म", "स्ते"]
    assert graphemes("abc") == ["a", "b", "c"]
    assert graphemes("") == []


def test_stats_counts():
    s = stats("ಕನ್ನಡ")
    assert (s.chars, s.graphemes, s.words, s.utf8_bytes) == (5, 3, 1, 15)
    assert stats("hello").utf8_bytes == 5


# ---- normalisation -------------------------------------------------------
def test_digits_roundtrip_all_scripts():
    for script in ("devanagari", "bengali", "gurmukhi", "gujarati", "odia", "tamil", "telugu", "kannada", "malayalam"):
        native = to_native_digits("0123456789", script)
        assert native != "0123456789" and len(native) == 10
        assert to_ascii_digits(native) == "0123456789"
    assert to_native_digits("2024", "kannada") == "೨೦೨೪"
    with pytest.raises(ValueError):
        to_native_digits("1", "klingon")


def test_normalize():
    assert normalize("ಕನ್ನಡ\u200b  ಭಾಷೆ") == "ಕನ್ನಡ ಭಾಷೆ"
    assert normalize("\ufeffಕ") == "ಕ"
    assert normalize("೧೨೩", digits="ascii") == "123"
    assert normalize("123", digits="devanagari") == "१२३"
    assert normalize("आज।") == "आज।"
    assert normalize("आज। कल॥", danda=True) == "आज. कल."
    assert "\u200d" in normalize("a\u200db") and "\u200d" not in normalize("a\u200db", keep_joiners=False)
    # NFC: decomposed nukta forms are composed where Unicode allows
    assert normalize("e\u0301") == "\u00e9"
    assert normalize("a \n  b\t c") == "a\nb c"


# ---- transliteration -----------------------------------------------------
def test_known_conversions():
    assert transliterate("namaste", "itrans", "devanagari") == "नमस्ते"
    assert transliterate("namaste", "itrans", "kannada") == "ನಮಸ್ತೇ"
    assert transliterate("namastE", "itrans", "kannada") == "ನಮಸ್ತೆ"      # E = short e (Dravidian)
    assert transliterate("kRRipayaa", "itrans", "devanagari") == "कृपया"
    assert transliterate("kSha", "itrans", "devanagari") == "क्ष"
    assert transliterate("bhaarata", "itrans", "malayalam") == "ഭാരത"
    assert transliterate("raama", "itrans", "tamil") == "ராம"
    assert transliterate("saMgiita", "itrans", "devanagari") == "संगीत"


def test_script_to_script_and_back():
    assert convert_script("ಕನ್ನಡ", "devanagari") == "कन्नड"
    assert convert_script("कन्नड", "kannada") == "ಕನ್ನಡ"
    assert convert_script("நன்றி", "devanagari") == "नऩ्ऱि"
    assert convert_script("mixed ಕ 123!", "devanagari") == "mixed क 123!"   # non-Brahmic untouched


def test_tamil_target_is_lossy_but_valid():
    out = convert_script("भारत", "tamil")           # bha -> pa
    assert out == "பாரத"


@pytest.mark.parametrize("word", ["namaste", "dhanyavaada", "bhaarata", "vidyaarthii", "kRRipayaa", "sundara", "praarthanaa", "saMgiita", "kSha", "ShaTkoNa", "hRRidaya"])
def test_itrans_roundtrip_via_every_script(word):
    for script in ("devanagari", "bengali", "gurmukhi", "gujarati", "odia", "telugu", "kannada", "malayalam"):
        assert to_latin(from_latin(word, script)) == word, (word, script)


def test_latin_edge_cases():
    assert from_latin("", "kannada") == ""
    assert from_latin("hello, namaste 123!", "devanagari") == "हेल्लो, नमस्ते 123!"  # ITRANS reads every letter
    assert transliterate("x", "kannada", "kannada") == "x"
    with pytest.raises(ValueError):
        transliterate("a", "itrans", "klingon")
    assert from_latin("aM", "devanagari") == "अं" and from_latin("kaH", "devanagari") == "कः"
    assert from_latin("|", "devanagari") == "।"
    # trailing consonant keeps its inherent vowel; consonant clusters get a virama
    assert from_latin("raam", "devanagari") == from_latin("raama", "devanagari") == "राम"
    assert from_latin("raam raam!", "devanagari") == "राम राम!"


# ---- token tax -----------------------------------------------------------
def test_token_tax_bytes_is_exact_and_english_is_one():
    rows = {r["code"]: r for r in token_tax("bytes")}
    assert rows["en"]["ratio_vs_english"] == 1.0
    assert all(rows[c]["ratio_vs_english"] > 2.0 for c in rows if c != "en")   # 3 bytes/char scripts
    expected = sum(len(s.encode()) for s in PARALLEL["kn"]) / sum(len(s.encode()) for s in PARALLEL["en"])
    assert rows["kn"]["ratio_vs_english"] == pytest.approx(expected)


def test_tokenizer_registry_and_errors():
    register_tokenizer("fake", lambda t: len(t.split()))
    assert count_tokens("a b c", "fake") == 3
    assert count_tokens("ab", "chars") == 2 and count_tokens("ಕನ್ನಡ", "graphemes") == 3
    with pytest.raises(ValueError, match="unknown tokenizer"):
        count_tokens("x", "nope")
    assert token_tax("fake", ["kn"])[0]["code"] == "en"  # English always included as the reference


def test_tiktoken_adapter_with_stub(monkeypatch):
    import sys, types
    stub = types.ModuleType("tiktoken")
    stub.get_encoding = lambda name: types.SimpleNamespace(encode=lambda t: list(range(len(t) // 2)))
    monkeypatch.setitem(sys.modules, "tiktoken", stub)
    assert count_tokens("abcdef", "tiktoken:whatever") == 3


def test_hf_adapter_with_stub(monkeypatch):
    import sys, types
    stub = types.ModuleType("tokenizers")
    class T:
        @staticmethod
        def from_pretrained(name):
            return types.SimpleNamespace(encode=lambda t, add_special_tokens=False: types.SimpleNamespace(ids=[1] * 7))
    stub.Tokenizer = T
    monkeypatch.setitem(sys.modules, "tokenizers", stub)
    assert count_tokens("anything", "hf:org/model") == 7


# ---- corpus sanity -------------------------------------------------------
def test_corpus_text_is_in_the_declared_script():
    from indickit.metrics import script_fidelity
    for code, (name, script) in LANGUAGES.items():
        for s in PARALLEL[code]:
            assert script_fidelity(s, script) > 0.99, (code, s)
