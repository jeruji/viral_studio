from __future__ import annotations

from pathlib import Path
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report


DATASET_PATH = Path(r"C:\Users\Public\Documents\sentimentdataset.csv")
MODEL_OUT = Path("models/sentiment_model.pkl")


def _clean_label(label: str) -> str:
    t = (label or "").strip().lower()
    if "neg" in t:
        return "negative"
    if "pos" in t:
        return "positive"
    return "neutral"


def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)
    if "Text" not in df.columns or "Sentiment" not in df.columns:
        raise RuntimeError("Expected columns: Text, Sentiment")

    df["Sentiment"] = df["Sentiment"].apply(_clean_label)
    X = df["Text"].fillna("").astype(str)
    y = df["Sentiment"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    vect = TfidfVectorizer(
        lowercase=True,
        max_features=5000,
        ngram_range=(1, 2)
    )
    X_train_vec = vect.fit_transform(X_train)
    X_test_vec = vect.transform(X_test)

    model = LogisticRegression(max_iter=2000, n_jobs=-1)
    model.fit(X_train_vec, y_train)

    preds = model.predict(X_test_vec)
    print(classification_report(y_test, preds))

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"model": model, "vectorizer": vect, "labels": ["negative", "neutral", "positive"]},
        MODEL_OUT
    )
    print(f"[OK] Saved: {MODEL_OUT}")


if __name__ == "__main__":
    main()
