import re
import json
import os
from pathlib import Path

CTA_PATTERNS = [
    r"\bfollow\b", r"\blike\b", r"\bshare\b", r"\bcomment\b", r"\bsave\b",
    r"\bsubscribe\b", r"\btag\b", r"\bduet\b", r"\bstitch\b",
    r"\bfyp\b", r"\bfor you\b",
    r"\bcek\b", r"\bcek\b", r"\blike dong\b", r"\bkomen\b", r"\bshare\b",
    r"\bsubscribe\b", r"\btag temen\b", r"\bkomen ya\b"
]

# sentiment_code sederhana:
# 0=negative/sad, 1=neutral, 2=positive/hype
POS_WORDS = {"happy", "hype", "party", "dance", "love", "senang", "semangat", "mantap", "gas"}
NEG_WORDS = {"sad", "cry", "hurt", "alone", "broken", "sedih", "kecewa", "patah", "galau", "nangis"}

def _load_keyword_features():
    out_dir = Path(os.getenv("OUTPUT_DIR", "outputs"))
    candidates = [
        out_dir / "patterns" / "feature_keywords.json",
        Path("config") / "feature_keywords.json",
    ]
    for p in candidates:
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                return {}
    return {}

_KW_FEATURES = _load_keyword_features()

def extract_text_features(text: str) -> dict:
    t = (text or "").lower()

    has_cta = 0
    for pat in CTA_PATTERNS:
        if re.search(pat, t):
            has_cta = 1
            break

    pos = sum(1 for w in POS_WORDS if w in t)
    neg = sum(1 for w in NEG_WORDS if w in t)

    if pos > neg and pos > 0:
        sentiment_code = 2
    elif neg > pos and neg > 0:
        sentiment_code = 0
    else:
        sentiment_code = 1

    feats = {
        "has_cta": float(has_cta),
        "sentiment_code": float(sentiment_code),
    }
    # Optional keyword features
    for key, kws in (_KW_FEATURES or {}).items():
        if not isinstance(kws, list):
            continue
        feats[f"kw_{key}"] = float(any(k in t for k in kws))
    return feats
