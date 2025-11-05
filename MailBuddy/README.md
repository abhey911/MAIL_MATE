# Mail Mate — Streamlit UI update (Add info + Classifier)

This adds a streamlined Streamlit app (streamlit_app.py) and a small classifier helper (mailmate/classifier.py).

How to run locally
1. Create virtualenv and install dependencies:
   python -m venv .venv
   source .venv/bin/activate   # (Linux / macOS)
   .venv\Scripts\activate      # (Windows)
   pip install -r requirements.txt

2. Start the app:
   streamlit run streamlit_app.py

What the UI does
- "Add info" section (contains the single Generate response button you wanted kept in that place).
- "Classify email" section (no Generate response button). You can point to a model path or upload a model file.
- Debug checkbox to show additional model info and traces.

Model format
- The app expects a pickled scikit-learn pipeline (pickle or joblib). The simplest compatible object is a Pipeline containing a vectorizer (TfidfVectorizer) and a classifier (e.g., LogisticRegression, RandomForestClassifier).
- Example saving code (in Python):
```python
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib

pipe = Pipeline([
    ("tfidf", TfidfVectorizer()),
    ("clf", LogisticRegression(max_iter=1000))
])
# after training:
joblib.dump(pipe, "models/email_classifier.pkl")
```

Troubleshooting classifier fails
- Confirm the model file exists at the path given to the UI (models/email_classifier.pkl by default).
- If using an uploaded file, make sure it's a pickled/sklearn-compatible object.
- If classification raises an exception, check the terminal where streamlit was started — errors and stack traces will appear there; enable the "Show debug info/tracebacks" checkbox in the UI for more info displayed in the app.