from difflib import SequenceMatcher
import re

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

def diff_ratio(a: str, b: str) -> float:
    return SequenceMatcher(a=normalize_arabic(a), b=normalize_arabic(b)).ratio()

def word_diffs(a: str, b: str):
    A = normalize_arabic(a).split()
    B = normalize_arabic(b).split()
    sm = SequenceMatcher(a=A, b=B)
    diffs = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal": continue
        diffs.append({
            "op": tag,
            "a": A[i1:i2],
            "b": B[j1:j2],
        })
    return diffs
