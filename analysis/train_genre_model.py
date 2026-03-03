from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report


DATASET_PATH = Path("data/archive/Data/features_3_sec.csv")
MODEL_OUT = Path("models/genre_model.pkl")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=str(DATASET_PATH), help="Path to GTZAN features_3_sec.csv")
    parser.add_argument("--out", default=str(MODEL_OUT), help="Path to output model .pkl")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    model_out = Path(args.out)

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    df = pd.read_csv(dataset_path)

    target_col = "label" if "label" in df.columns else "music_genre" if "music_genre" in df.columns else None
    if target_col is None:
        raise RuntimeError("Missing target column: expected `label` (GTZAN) or `music_genre`.")

    ignore_cols = {"filename", "label", "length", "music_genre", "instance_id", "artist_name", "track_name", "key", "mode", "obtained_date"}
    feature_cols = [c for c in df.columns if c not in ignore_cols]
    if not feature_cols:
        raise RuntimeError("No usable feature columns found in genre dataset.")

    raw_y = df[target_col].copy()
    keep_mask = raw_y.notna()
    X = df.loc[keep_mask, feature_cols].copy()
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    y = raw_y.loc[keep_mask].astype(str).str.strip().str.lower()
    y = y.replace({"hip hop": "hiphop", "hip-hop": "hiphop"})
    valid_mask = ~y.isin(["", "nan", "none", "null"])
    X = X.loc[valid_mask].reset_index(drop=True)
    y = y.loc[valid_mask].reset_index(drop=True)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=600,
        max_depth=None,
        min_samples_leaf=1,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced_subsample",
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print(classification_report(y_test, preds))

    # Quick visibility for debugging feature importance.
    importances = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
    print("\nTop 20 feature importances:")
    for name, score in importances.head(20).items():
        print(f"- {name}: {score:.6f}")

    model_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_out)
    print(f"[OK] Saved: {model_out}")


if __name__ == "__main__":
    main()
