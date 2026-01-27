import joblib
import pandas as pd

class ViralityScorer:
    def __init__(self):
        try:
            self.virality_model = joblib.load("models/virality_model.pkl")
            self.genre_model = joblib.load("models/genre_model.pkl")
            self.audience_model = joblib.load("models/audience_model.pkl")
        except Exception:
            self.virality_model = None
            self.genre_model = None
            self.audience_model = None
        self.genre_map = {
            0: "jedag_jedug",
            1: "tiktok_house",
            2: "lofi_chill",
            3: "mellow_rainy",
            4: "cinematic_epic",
        }
        self.audience_map = {
            0: "gen_z",
            1: "young_adult",
            2: "music_enthusiast",
            3: "casual_scroller",
            4: "story_seeker",
        }

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

        proba = self.virality_model.predict_proba(Xv)[0]
        # ambil proba kelas 1 kalau ada
        classes = list(getattr(self.virality_model, "classes_", [0, 1]))
        idx = classes.index(1) if 1 in classes else (1 if len(proba) > 1 else 0)

        genre_id = int(self.genre_model.predict(Xg)[0])
        audience_id = int(self.audience_model.predict(Xa)[0])
        return {
            "virality_score": float(proba[idx] * 100.0),
            "genre": genre_id,
            "genre_label": self.genre_map.get(genre_id, f"unknown_{genre_id}"),
            "audience": audience_id,
            "audience_label": self.audience_map.get(audience_id, f"unknown_{audience_id}"),
        }
