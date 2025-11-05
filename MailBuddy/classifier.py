# Helper classifier functions used by the Streamlit app.
# Place this file at mailmate/classifier.py in the repo.

import pickle
import traceback
from typing import Any, Dict, Optional

def load_model_from_path(path: str) -> Optional[Any]:
    """
    Load a pickled model from disk and return it.
    Returns None on failure.
    """
    try:
        with open(path, "rb") as f:
            model = pickle.load(f)
        return model
    except Exception:
        # Caller can enable debug to see details
        return None

def load_model_from_bytes(data: bytes) -> Optional[Any]:
    """
    Load a pickled model from raw bytes (useful for uploaded files).
    """
    try:
        model = pickle.loads(data)
        return model
    except Exception:
        return None

def preprocess_text(text: str) -> str:
    """
    Minimal preprocessing. Adapt to your real train-time preprocessing (lowercase, remove signatures, tokenize, etc).
    """
    if text is None:
        return ""
    return text.strip()

def classify_with_model(model: Any, text: str) -> Dict:
    """
    Perform classification with defensive programming and return a dict:
      - {'label': ..., 'confidence': float} on success
      - {'error': '...'} on failure
    This function supports:
      - scikit-learn pipelines that accept raw text (pipeline = [TfidfVectorizer, clf])
      - simple classifiers requiring pre-vectorized input if provided as such (you would need to adapt)
    """
    try:
        if model is None:
            return {"error": "Model is None"}

        X = [text]

        # If model exposes predict_proba
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(X)[0]
            idx = int(probs.argmax())
            label = model.classes_[idx] if hasattr(model, "classes_") else idx
            return {"label": label, "confidence": float(probs.max())}

        # Otherwise fallback to predict
        if hasattr(model, "predict"):
            pred = model.predict(X)[0]
            return {"label": pred, "confidence": None}

        return {"error": "Model has no predict or predict_proba method"}
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}