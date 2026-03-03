import joblib
import pandas as pd
import numpy as np

class ViralityScorer:
    def __init__(self):
        self.virality_calibration = None
        try:
            v_obj = joblib.load("models/virality_model.pkl")
            if isinstance(v_obj, dict) and "model" in v_obj:
                self.virality_model = v_obj.get("model")
                self.virality_calibration = v_obj.get("calibration")
            else:
                self.virality_model = v_obj
            self.genre_model = joblib.load("models/genre_model.pkl")
            self.audience_model = joblib.load("models/audience_model.pkl")
        except Exception:
            self.virality_model = None
            self.genre_model = None
            self.audience_model = None
            self.virality_calibration = None
        self.genre_map = {
            0: "blues",
            1: "classical",
            2: "country",
            3: "disco",
            4: "hiphop",
            5: "jazz",
            6: "metal",
            7: "pop",
            8: "reggae",
            9: "rock",
        }
        self.audience_map = {
            0: "gen_z",
            1: "young_adult",
            2: "music_enthusiast",
            3: "casual_scroller",
            4: "story_seeker",
        }
        self.genre_rev = {v: k for k, v in self.genre_map.items()}

    def _make_X(self, model, feats: dict) -> pd.DataFrame:
        cols = list(getattr(model, "feature_names_in_", []))
        if not cols:
            # fallback (harusnya tidak kejadian di model kamu)
            cols = sorted(feats.keys())

        row = {c: float(feats.get(c, 0.0)) for c in cols}
        return pd.DataFrame([row], columns=cols)

    def predict(self, feats: dict) -> dict:
        if not self.virality_model or not self.genre_model or not self.audience_model:
            return {
                "virality_score": 50.0,
                "genre": -1,
                "genre_label": "unknown",
                "audience": -1,
                "audience_label": "unknown",
            }
        Xv = self._make_X(self.virality_model, feats)
        Xg = self._make_X(self.genre_model, feats)
        Xa = self._make_X(self.audience_model, feats)

        # Handle classifier (predict_proba) vs regressor (predict)
        if hasattr(self.virality_model, "predict_proba"):
            proba = self.virality_model.predict_proba(Xv)[0]
            # ambil proba kelas 1 kalau ada
            classes = list(getattr(self.virality_model, "classes_", [0, 1]))
            idx = classes.index(1) if 1 in classes else (1 if len(proba) > 1 else 0)
            virality_score = float(proba[idx] * 100.0)
        else:
            pred = float(self.virality_model.predict(Xv)[0])
            # Regression calibrated to dataset percentile (ECDF) when available.
            cal = self.virality_calibration if isinstance(self.virality_calibration, dict) else {}
            y_sorted = np.asarray(cal.get("y_sorted", []), dtype=float)
            if y_sorted.size > 0:
                rank = np.searchsorted(y_sorted, pred, side="right")
                virality_score = float((rank / y_sorted.size) * 100.0)
            else:
                pred = max(0.0, pred)
                virality_score = max(0.0, min(100.0, pred * 100.0))

        genre_pred = self.genre_model.predict(Xg)[0]
        if isinstance(genre_pred, str):
            genre_label = genre_pred.strip().lower().replace("hip hop", "hiphop").replace("hip-hop", "hiphop")
            genre_id = int(self.genre_rev.get(genre_label, -1))
        else:
            genre_id = int(genre_pred)
            genre_label = self.genre_map.get(genre_id, f"unknown_{genre_id}")

        audience_pred = self.audience_model.predict(Xa)[0]
        if isinstance(audience_pred, str):
            # fallback if audience model ever returns string labels
            aud_rev = {v: k for k, v in self.audience_map.items()}
            audience_label = audience_pred.strip().lower()
            audience_id = int(aud_rev.get(audience_label, -1))
        else:
            audience_id = int(audience_pred)
            audience_label = self.audience_map.get(audience_id, f"unknown_{audience_id}")
        return {
            "virality_score": virality_score,
            "genre": genre_id,
            "genre_label": genre_label,
            "audience": audience_id,
            "audience_label": audience_label,
        }
