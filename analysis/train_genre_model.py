from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report


DATASET_PATH = Path(r"C:\Users\Public\Documents\Data\features_3_sec.csv")
MODEL_OUT = Path("models/genre_model.pkl")


def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)

    # Map GTZAN feature names -> pipeline feature names
    feature_map = {
        "rms_mean": "rms",
        "spectral_centroid_mean": "spectral_centroid",
        "tempo": "bpm",
    }

    missing = [c for c in feature_map.keys() if c not in df.columns]
    if missing:
        raise RuntimeError(f"Missing columns in dataset: {missing}")

    X = df[list(feature_map.keys())].rename(columns=feature_map)
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print(classification_report(y_test, preds))

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_OUT)
    print(f"[OK] Saved: {MODEL_OUT}")


if __name__ == "__main__":
    main()
