import os
import joblib
import numpy as np
from pathlib import Path
MODEL_PATH = str(Path(__file__).resolve().parents[2] / "data" / "ml" / "trust_model.joblib")

_model = None

def _load_model():
    global _model
    if _model is None and os.path.exists(MODEL_PATH):
        _model = joblib.load(MODEL_PATH)
    return _model

def predict_trust(question: str, top_distance: float | None, has_retrieval: bool, comment: str | None = None):
    model = _load_model()
    if model is None:
        return None

    question_len = len(question or "")
    comment_len = len(comment or "")
    td = float(top_distance) if top_distance is not None else 9999.0
    X = np.array([[question_len, td, int(has_retrieval), comment_len]], dtype=float)

    return float(model.predict_proba(X)[0, 1])