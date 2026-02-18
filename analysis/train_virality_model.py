from __future__ import annotations

from pathlib import Path
import re
import json
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score


DATASET_PATH = Path(r"C:\Users\Public\Documents\Social Media Engagement Dataset.csv")
MODEL_OUT = Path("models/virality_model.pkl")

# Keep feature set aligned with runtime features in main.py + ml/feature_text.py
BASE_FEATURES = [
    "bpm",
    "rms",
    "duration_sec",
    "spectral_centroid",
    "avg_brightness",
    "cut_rate_per_min",
    "has_faces",
    "has_text_overlay",
    "has_cta",
    "sentiment_code",
    "text_len",
    "word_count",
    "hashtag_count",
    "mention_count",
    "exclam_count",
    "question_count",
    "avg_word_len",
    "platform_instagram",
    "platform_tiktok",
    "platform_twitter",
    "platform_facebook",
    "platform_youtube",
    "platform_reddit",
    "day_0",
    "day_1",
    "day_2",
    "day_3",
    "day_4",
    "day_5",
    "day_6",
    "toxicity_score",
    "emotion_type_id",
]

CTA_PATTERNS = [
    r"\bfollow\b", r"\blike\b", r"\bshare\b", r"\bcomment\b", r"\bsave\b",
    r"\bsubscribe\b", r"\btag\b", r"\bduet\b", r"\bstitch\b",
    r"\bfyp\b", r"\bfor you\b",
    r"\bcek\b", r"\bcek\b", r"\blike dong\b", r"\bkomen\b", r"\bshare\b",
    r"\bsubscribe\b", r"\btag temen\b", r"\bkomen ya\b"
]


def _load_keyword_features():
    out_dir = Path("outputs")
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


def _has_cta(text: str) -> float:
    t = (text or "").lower()
    for pat in CTA_PATTERNS:
        if re.search(pat, t):
            return 1.0
    return 0.0


def _text_stats(text: str) -> dict:
    t = (text or "")
    words = re.findall(r"\w+", t.lower())
    hashtag_count = len(re.findall(r"#\w+", t))
    mention_count = len(re.findall(r"@\w+", t))
    exclam_count = t.count("!")
    question_count = t.count("?")
    avg_word_len = (sum(len(w) for w in words) / len(words)) if words else 0.0
    return {
        "text_len": float(len(t)),
        "word_count": float(len(words)),
        "hashtag_count": float(hashtag_count),
        "mention_count": float(mention_count),
        "exclam_count": float(exclam_count),
        "question_count": float(question_count),
        "avg_word_len": float(avg_word_len),
    }


def _one_hot_platform(platform: str) -> dict:
    t = (platform or "").strip().lower()
    keys = {
        "instagram": "platform_instagram",
        "tiktok": "platform_tiktok",
        "twitter": "platform_twitter",
        "facebook": "platform_facebook",
        "youtube": "platform_youtube",
        "reddit": "platform_reddit",
    }
    out = {v: 0.0 for v in keys.values()}
    for k, v in keys.items():
        if k in t:
            out[v] = 1.0
            break
    return out


def _day_of_week_one_hot(day: str) -> dict:
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    out = {f"day_{i}": 0.0 for i in range(7)}
    t = (day or "").strip().lower()
    if t in days:
        out[f"day_{days.index(t)}"] = 1.0
    return out


def _emotion_id(emotion: str) -> float:
    emotions = ["neutral", "happy", "sad", "angry", "fear", "surprise", "disgust", "confused"]
    t = (emotion or "").strip().lower()
    return float(emotions.index(t)) if t in emotions else 0.0


def _sentiment_code(label: str) -> float:
    t = (label or "").strip().lower()
    if "neg" in t:
        return 0.0
    if "pos" in t:
        return 2.0
    return 1.0


def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)

    # Build a single text field for CTA/keyword detection
    text = (
        df.get("text_content", "").astype(str)
        + " "
        + df.get("hashtags", "").astype(str)
        + " "
        + df.get("keywords", "").astype(str)
    )

    # Engagement rate (target)
    if "engagement_rate" in df.columns:
        engagement = pd.to_numeric(df["engagement_rate"], errors="coerce")
    else:
        likes = pd.to_numeric(df.get("likes_count", 0), errors="coerce")
        shares = pd.to_numeric(df.get("shares_count", 0), errors="coerce")
        comments = pd.to_numeric(df.get("comments_count", 0), errors="coerce")
        impressions = pd.to_numeric(df.get("impressions", 0), errors="coerce")
        engagement = (likes + shares + comments) / impressions.replace(0, pd.NA)

    engagement = engagement.replace([pd.NA, pd.NaT], pd.NA).astype("float64")
    engagement = engagement.dropna()

    # Align df to valid engagement rows
    df = df.loc[engagement.index]
    text = text.loc[engagement.index]

    # Regression target: engagement_rate (continuous)
    y = engagement.astype("float64")

    # Build features aligned with runtime
    feats = {}
    feats["has_cta"] = text.apply(_has_cta)
    feats["sentiment_code"] = df.get("sentiment_label", "").apply(_sentiment_code)
    stats = text.apply(_text_stats)
    feats["text_len"] = stats.apply(lambda x: x["text_len"])
    feats["word_count"] = stats.apply(lambda x: x["word_count"])
    feats["hashtag_count"] = stats.apply(lambda x: x["hashtag_count"])
    feats["mention_count"] = stats.apply(lambda x: x["mention_count"])
    feats["exclam_count"] = stats.apply(lambda x: x["exclam_count"])
    feats["question_count"] = stats.apply(lambda x: x["question_count"])
    feats["avg_word_len"] = stats.apply(lambda x: x["avg_word_len"])

    platform_stats = df.get("platform", "").apply(_one_hot_platform)
    for k in ["platform_instagram", "platform_tiktok", "platform_twitter", "platform_facebook", "platform_youtube", "platform_reddit"]:
        feats[k] = platform_stats.apply(lambda x: x.get(k, 0.0))

    day_stats = df.get("day_of_week", "").apply(_day_of_week_one_hot)
    for i in range(7):
        feats[f"day_{i}"] = day_stats.apply(lambda x: x.get(f"day_{i}", 0.0))

    feats["toxicity_score"] = pd.to_numeric(df.get("toxicity_score", 0.0), errors="coerce").fillna(0.0)
    feats["emotion_type_id"] = df.get("emotion_type", "").apply(_emotion_id)

    kw_features = _load_keyword_features()
    for key, kws in (kw_features or {}).items():
        if not isinstance(kws, list):
            continue
        feats[f"kw_{key}"] = text.str.lower().apply(lambda t: float(any(k in t for k in kws)))

    # Audio/video features not in dataset -> zeros
    feats["bpm"] = 0.0
    feats["rms"] = 0.0
    feats["duration_sec"] = 0.0
    feats["spectral_centroid"] = 0.0
    feats["avg_brightness"] = 0.0
    feats["cut_rate_per_min"] = 0.0
    feats["has_faces"] = 0.0
    feats["has_text_overlay"] = 0.0

    X = pd.DataFrame(feats)

    # Ensure all base features exist even if kw_* absent
    for col in BASE_FEATURES:
        if col not in X.columns:
            X[col] = 0.0

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=400,
        max_depth=None,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    print(f"[INFO] MAE: {mae:.4f}")
    print(f"[INFO] R2:  {r2:.4f}")

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_OUT)
    print(f"[OK] Saved: {MODEL_OUT}")


if __name__ == "__main__":
    main()
