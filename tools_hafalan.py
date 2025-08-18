import re
from difflib import SequenceMatcher

# -------- Normalisasi Arab (buang harakat dsb) --------
_ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
_TATWEEL = "\u0640"

def normalize_arabic(s: str) -> str:
    if not s: return ""
    s = s.replace(_TATWEEL, "")
    s = _ARABIC_DIACRITICS.sub("", s)
    s = s.replace("أ","ا").replace("إ","ا").replace("آ","ا")
    s = s.replace("ى","ي").replace("ة","ه")
    s = re.sub(r"[^ء-ي\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

# -------- Transliterasi Arab -> Latin (skema sederhana Indonesia) --------
_MAP_AR2LAT = {
    "ا":"a", "ب":"b", "ت":"t", "ث":"ts", "ج":"j", "ح":"h", "خ":"kh",
    "د":"d", "ذ":"dz", "ر":"r", "ز":"z", "س":"s", "ش":"sy",
    "ص":"s", "ض":"d", "ط":"t", "ظ":"z", "ع":"",  "غ":"gh",
    "ف":"f", "ق":"q", "ك":"k", "ل":"l", "م":"m", "ن":"n",
    "ه":"h", "و":"w", "ي":"y", "ء":"'", "ٱ":"a",
}

def arabic_to_latin_basic(s: str) -> str:
    s = normalize_arabic(s)
    out = []
    for ch in s:
        out.append(_MAP_AR2LAT.get(ch, ch))
    return re.sub(r"\s+", " ", "".join(out)).strip()

# -------- Normalisasi Latin user (sy/sh -> diseragamkan, dll) --------
def normalize_latin_user(s: str) -> str:
    if not s: return ""
    s = s.lower().strip()
    # seragamkan variasi umum
    s = s.replace("sh", "sy")   # pengguna kadang tulis "sh"
    s = s.replace("dz", "dz")   # biarkan, hanya placeholder biar konsisten
    s = s.replace("th", "t")    # hindari ambigu (ط/ث), sederhanakan
    s = s.replace("aa", "a")    # panjang vokal disederhanakan
    s = re.sub(r"[^a-z'\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

# -------- Pembanding fleksibel --------
def diff_ratio(a_target_arabic: str, b_user: str, mode: str) -> float:
    """
    mode = 'arabic'  -> bandingkan arabic vs arabic
    mode = 'latin'   -> translit target -> latin, user latin -> latin, lalu bandingkan
    """
    if mode == "latin":
        A = arabic_to_latin_basic(a_target_arabic)
        B = normalize_latin_user(b_user)
    else:
        A = normalize_arabic(a_target_arabic)
        B = normalize_arabic(b_user)
    return SequenceMatcher(a=A, b=B).ratio()

def word_diffs(a_target_arabic: str, b_user: str, mode: str):
    if mode == "latin":
        A = arabic_to_latin_basic(a_target_arabic).split()
        B = normalize_latin_user(b_user).split()
    else:
        A = normalize_arabic(a_target_arabic).split()
        B = normalize_arabic(b_user).split()

    sm = SequenceMatcher(a=A, b=B)
    diffs = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal": continue
        diffs.append({"op": tag, "a": A[i1:i2], "b": B[j1:j2]})
    return diffs
