from pathlib import Path
from ml.feature_video import extract_video_features
try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None
import numpy as np
import os

# load once (biar cepat); fall back if model can't load (e.g., low memory)
_EMB = None
if SentenceTransformer is not None:
    try:
        _EMB = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    except Exception:
        _EMB = None

def _sim(a: str, b: str) -> float:
    """Cosine similarity 0..1-ish."""
    if not a or not b:
        return 0.0
    if _EMB is None:
        return 0.0
    ea = _EMB.encode([a], normalize_embeddings=True)[0]
    eb = _EMB.encode([b], normalize_embeddings=True)[0]
    return float(np.dot(ea, eb))

def _video_path(v):
    # v can be dict or str
    if isinstance(v, (str, Path)):
        return str(v)
    if isinstance(v, dict):
        # prefer final_path if you have it later
        return str(v.get("final_path") or v.get("path") or "")
    return ""

def select_best(videos, scorer, base_features):
    best = None
    best_score = -1e9

    # Target text: makin kaya makin bagus (lyrics + mood + platform + caption/style)
    # Pastikan di main.py kamu memasukkan ini ke base_features:
    # base_features["_target_text"] = f"{platform}\n{mood}\n{caption}\n{audio_style}\n{lyrics}"
    target_text = (base_features.get("_target_text") or "").strip()

    for v in videos:
        p = _video_path(v)
        if not p:
            continue
        if not os.path.exists(p):
            # skip yang belum benar-benar ada
            continue

        vf = extract_video_features(p)
        features = {**base_features, **vf}

        # ML virality score (0..100 assumed)
        ml_score = float(scorer.predict(features)["virality_score"])

        # Prompt kandidat (dari LLM)
        prompt_text = ""
        if isinstance(v, dict):
            prompt_text = (v.get("prompt") or "").strip()

        # Semantic relevance 0..1
        rel = _sim(target_text, prompt_text) if (target_text and prompt_text) else 0.0
        rel_score = rel * 100.0

        # Hard penalty untuk out-of-context (opsional tapi berguna)
        ptext_l = prompt_text.lower()
        bad = ["sawah", "rice field", "paddy", "farm", "countryside"]
        bad_penalty = 80.0 if any(k in ptext_l for k in bad) else 0.0

        # Final score: gabungan "viral" + "nyambung"
        # kamu bisa tweak bobotnya
        score = (0.70 * ml_score) + (0.30 * rel_score) - bad_penalty

        if score > best_score:
            best_score = score
            best = v

    return best, best_score


