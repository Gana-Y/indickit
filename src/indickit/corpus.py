"""A tiny parallel corpus: the same 6 everyday sentences in English and 10 Indian languages.

IMPORTANT: this is a *seed* set, drafted with AI assistance and **not yet verified by native
speakers**. Translations of such short, simple sentences are usually fine, but a few may be
unnatural. Reviewing them is the easiest way to contribute (see CONTRIBUTING.md).
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# code -> (English name, script)
LANGUAGES: Dict[str, Tuple[str, str]] = {
    "en": ("English", "latin"),
    "hi": ("Hindi", "devanagari"),
    "mr": ("Marathi", "devanagari"),
    "bn": ("Bengali", "bengali"),
    "pa": ("Punjabi", "gurmukhi"),
    "gu": ("Gujarati", "gujarati"),
    "or": ("Odia", "odia"),
    "ta": ("Tamil", "tamil"),
    "te": ("Telugu", "telugu"),
    "kn": ("Kannada", "kannada"),
    "ml": ("Malayalam", "malayalam"),
}

PARALLEL: Dict[str, List[str]] = {
    "en": [
        "Hello, how are you?",
        "Today the weather is very nice.",
        "I want to learn programming.",
        "Where is the nearest railway station?",
        "Thank you very much for your help.",
        "Please send me the bill by tomorrow.",
    ],
    "hi": [
        "नमस्ते, आप कैसे हैं?",
        "आज मौसम बहुत अच्छा है।",
        "मैं प्रोग्रामिंग सीखना चाहता हूँ।",
        "सबसे नज़दीकी रेलवे स्टेशन कहाँ है?",
        "आपकी मदद के लिए बहुत-बहुत धन्यवाद।",
        "कृपया कल तक मुझे बिल भेज दीजिए।",
    ],
    "mr": [
        "नमस्कार, तुम्ही कसे आहात?",
        "आज हवामान खूप छान आहे.",
        "मला प्रोग्रामिंग शिकायचं आहे.",
        "सर्वात जवळचे रेल्वे स्टेशन कुठे आहे?",
        "तुमच्या मदतीबद्दल खूप खूप धन्यवाद.",
        "कृपया उद्यापर्यंत मला बिल पाठवा.",
    ],
    "bn": [
        "নমস্কার, আপনি কেমন আছেন?",
        "আজ আবহাওয়া খুব সুন্দর।",
        "আমি প্রোগ্রামিং শিখতে চাই।",
        "সবচেয়ে কাছের রেলওয়ে স্টেশন কোথায়?",
        "আপনার সাহায্যের জন্য অনেক ধন্যবাদ।",
        "অনুগ্রহ করে আগামীকালের মধ্যে আমাকে বিলটি পাঠান।",
    ],
    "pa": [
        "ਸਤ ਸ੍ਰੀ ਅਕਾਲ, ਤੁਸੀਂ ਕਿਵੇਂ ਹੋ?",
        "ਅੱਜ ਮੌਸਮ ਬਹੁਤ ਵਧੀਆ ਹੈ।",
        "ਮੈਂ ਪ੍ਰੋਗਰਾਮਿੰਗ ਸਿੱਖਣਾ ਚਾਹੁੰਦਾ ਹਾਂ।",
        "ਸਭ ਤੋਂ ਨੇੜੇ ਦਾ ਰੇਲਵੇ ਸਟੇਸ਼ਨ ਕਿੱਥੇ ਹੈ?",
        "ਤੁਹਾਡੀ ਮਦਦ ਲਈ ਬਹੁਤ ਧੰਨਵਾਦ।",
        "ਕਿਰਪਾ ਕਰਕੇ ਕੱਲ੍ਹ ਤੱਕ ਮੈਨੂੰ ਬਿੱਲ ਭੇਜ ਦਿਓ।",
    ],
    "gu": [
        "નમસ્તે, તમે કેમ છો?",
        "આજે હવામાન ખૂબ સરસ છે.",
        "મારે પ્રોગ્રામિંગ શીખવું છે.",
        "સૌથી નજીકનું રેલવે સ્ટેશન ક્યાં છે?",
        "તમારી મદદ માટે ખૂબ ખૂબ આભાર.",
        "કૃપા કરીને આવતીકાલ સુધીમાં મને બિલ મોકલો.",
    ],
    "or": [
        "ନମସ୍କାର, ଆପଣ କେମିତି ଅଛନ୍ତି?",
        "ଆଜି ପାଗ ବହୁତ ସୁନ୍ଦର ଅଛି।",
        "ମୁଁ ପ୍ରୋଗ୍ରାମିଂ ଶିଖିବାକୁ ଚାହୁଁଛି।",
        "ସବୁଠାରୁ ପାଖ ରେଳ ଷ୍ଟେସନ କେଉଁଠି ଅଛି?",
        "ଆପଣଙ୍କ ସାହାଯ୍ୟ ପାଇଁ ବହୁତ ଧନ୍ୟବାଦ।",
        "ଦୟାକରି ଆସନ୍ତାକାଲି ସୁଦ୍ଧା ମୋତେ ବିଲ୍ ପଠାନ୍ତୁ।",
    ],
    "ta": [
        "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
        "இன்று வானிலை மிகவும் நன்றாக உள்ளது.",
        "நான் நிரலாக்கம் கற்றுக்கொள்ள விரும்புகிறேன்.",
        "அருகிலுள்ள ரயில் நிலையம் எங்கே இருக்கிறது?",
        "உங்கள் உதவிக்கு மிக்க நன்றி.",
        "தயவுசெய்து நாளைக்குள் எனக்கு பில் அனுப்புங்கள்.",
    ],
    "te": [
        "నమస్కారం, మీరు ఎలా ఉన్నారు?",
        "ఈ రోజు వాతావరణం చాలా బాగుంది.",
        "నేను ప్రోగ్రామింగ్ నేర్చుకోవాలనుకుంటున్నాను.",
        "సమీపంలోని రైల్వే స్టేషన్ ఎక్కడ ఉంది?",
        "మీ సహాయానికి చాలా ధన్యవాదాలు.",
        "దయచేసి రేపటిలోగా నాకు బిల్లు పంపండి.",
    ],
    "kn": [
        "ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ?",
        "ಇಂದು ಹವಾಮಾನ ತುಂಬಾ ಚೆನ್ನಾಗಿದೆ.",
        "ನಾನು ಪ್ರೋಗ್ರಾಮಿಂಗ್ ಕಲಿಯಲು ಬಯಸುತ್ತೇನೆ.",
        "ಹತ್ತಿರದ ರೈಲ್ವೆ ನಿಲ್ದಾಣ ಎಲ್ಲಿದೆ?",
        "ನಿಮ್ಮ ಸಹಾಯಕ್ಕೆ ತುಂಬಾ ಧನ್ಯವಾದಗಳು.",
        "ದಯವಿಟ್ಟು ನಾಳೆಯೊಳಗೆ ನನಗೆ ಬಿಲ್ ಕಳುಹಿಸಿ.",
    ],
    "ml": [
        "നമസ്കാരം, നിങ്ങൾക്ക് സുഖമാണോ?",
        "ഇന്ന് കാലാവസ്ഥ വളരെ നല്ലതാണ്.",
        "എനിക്ക് പ്രോഗ്രാമിംഗ് പഠിക്കണം.",
        "അടുത്തുള്ള റെയിൽവേ സ്റ്റേഷൻ എവിടെയാണ്?",
        "നിങ്ങളുടെ സഹായത്തിന് വളരെ നന്ദി.",
        "ദയവായി നാളെയ്ക്കുള്ളിൽ എനിക്ക് ബിൽ അയയ്ക്കൂ.",
    ],
}

assert all(len(v) == 6 for v in PARALLEL.values()) and set(PARALLEL) == set(LANGUAGES)

# ITRANS words used by the transliteration benchmark task: (ITRANS, English gloss)
TRANSLIT_WORDS = ["namaste", "dhanyavaada", "bhaarata", "vidyaarthii", "kRRipayaa", "sundara", "praarthanaa", "saMgiita"]
