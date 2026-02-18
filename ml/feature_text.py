import re
import json
import os
from pathlib import Path
import joblib
import numpy as np

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

EMOTION_MAP = {
    "happy": {"happy", "joy", "excited", "senang", "gembira", "bahagia", "seru"},
    "sad": {"sad", "cry", "sedih", "galau", "patah", "kecewa"},
    "angry": {"angry", "marah", "kesal", "benci"},
    "fear": {"fear", "takut", "ngeri", "khawatir"},
    "surprise": {"surprise", "kaget", "terkejut"},
    "disgust": {"disgust", "jijik"},
    "confused": {"confused", "bingung"},
}

TOXIC_WORDS = {
    "idiot", "stupid", "dumb", "moron", "bastard", "shit", "fuck", "bitch",
    "tolol", "bodoh", "goblok", "anjing", "bangsat", "kontol", "memek"
}

_SENTIMENT_MODEL = None
_SENTIMENT_VECT = None
_SENTIMENT_LABELS = None

def _load_sentiment_model():
    global _SENTIMENT_MODEL, _SENTIMENT_VECT, _SENTIMENT_LABELS
    if _SENTIMENT_MODEL is not None:
        return
    model_path = Path("models") / "sentiment_model.pkl"
    if not model_path.exists():
        return
    try:
        payload = joblib.load(model_path)
        _SENTIMENT_MODEL = payload.get("model")
        _SENTIMENT_VECT = payload.get("vectorizer")
        _SENTIMENT_LABELS = payload.get("labels") or ["negative", "neutral", "positive"]
    except Exception:
        _SENTIMENT_MODEL = None
        _SENTIMENT_VECT = None
        _SENTIMENT_LABELS = None

def _predict_sentiment_code(text: str) -> float:
    _load_sentiment_model()
    if not _SENTIMENT_MODEL or not _SENTIMENT_VECT:
        return -1.0
    try:
        X = _SENTIMENT_VECT.transform([text or ""])
        pred = _SENTIMENT_MODEL.predict(X)[0]
        label = str(pred).strip().lower()
        if "neg" in label:
            return 0.0
        if "pos" in label:
            return 2.0
        return 1.0
    except Exception:
        return -1.0

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

    sentiment_code = _predict_sentiment_code(text)
    if sentiment_code < 0:
        pos = sum(1 for w in POS_WORDS if w in t)
        neg = sum(1 for w in NEG_WORDS if w in t)

        if pos > neg and pos > 0:
            sentiment_code = 2
        elif neg > pos and neg > 0:
            sentiment_code = 0
        else:
            sentiment_code = 1

    # Emotion heuristic
    emotion_scores = {k: 0 for k in EMOTION_MAP.keys()}
    for emo, words_set in EMOTION_MAP.items():
        for w in words_set:
            if w in t:
                emotion_scores[emo] += 1
    if any(emotion_scores.values()):
        emotion_type = max(emotion_scores, key=emotion_scores.get)
    else:
        emotion_type = "neutral"

    emotion_index = {
        "neutral": 0,
        "happy": 1,
        "sad": 2,
        "angry": 3,
        "fear": 4,
        "surprise": 5,
        "disgust": 6,
        "confused": 7,
    }.get(emotion_type, 0)

    # Toxicity heuristic (0..1)
    tox_hits = sum(1 for w in TOXIC_WORDS if w in t)
    toxicity_score = min(1.0, tox_hits / 3.0)

    text_raw = text or ""
    words = re.findall(r"\w+", t)
    hashtag_count = len(re.findall(r"#\w+", text_raw))
    mention_count = len(re.findall(r"@\w+", text_raw))
    exclam_count = text_raw.count("!")
    question_count = text_raw.count("?")
    avg_word_len = (sum(len(w) for w in words) / len(words)) if words else 0.0

    feats = {
        "has_cta": float(has_cta),
        "sentiment_code": float(sentiment_code),
        "text_len": float(len(text_raw)),
        "word_count": float(len(words)),
        "hashtag_count": float(hashtag_count),
        "mention_count": float(mention_count),
        "exclam_count": float(exclam_count),
        "question_count": float(question_count),
        "avg_word_len": float(avg_word_len),
        "toxicity_score": float(toxicity_score),
        "emotion_type_id": float(emotion_index),
    }
    # Optional keyword features
    for key, kws in (_KW_FEATURES or {}).items():
        if not isinstance(kws, list):
            continue
        feats[f"kw_{key}"] = float(any(k in t for k in kws))
    return feats
