import re

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

    return {
        "has_cta": float(has_cta),
        "sentiment_code": float(sentiment_code),
    }
