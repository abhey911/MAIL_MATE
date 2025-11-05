import streamlit as st
import logging
import pickle
import tempfile
import os
from typing import Any, Dict, Optional

from classifier import load_model_from_path, load_model_from_bytes, classify_with_model, preprocess_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mailmate")

st.set_page_config(page_title="Mail Mate", layout="centered")
st.title("Mail Mate")

# -------------------------
# Add info section (KEEP Generate response here)
# -------------------------
st.header("Add info")
add_info = st.text_area("Add contextual information (used when generating replies)", key="add_info_text", height=120)

if st.button("Generate response", key="generate_response_add_info"):
    if not add_info or add_info.strip() == "":
        st.warning("Please add contextual information before generating a response.")
    else:
        # Placeholder generation logic - replace with real generator call
        reply = f"(placeholder) Generated reply using context:\n\n{add_info.strip()[:200]}..."
        st.success("Generated response")
        st.code(reply)

st.markdown("---")

# -------------------------
# Classify email section (NO Generate response here)
# -------------------------
st.header("Classify email")
email_text = st.text_area("Paste the email you want classified", key="email_to_classify", height=200)

st.write("Model source (choose one):")
col1, col2 = st.columns(2)

model_from_repo = col1.text_input("Path to model file (relative to repo/run dir)", value="models/email_classifier.pkl", key="model_path")
uploaded_model = col2.file_uploader("Or upload model (.pkl/.joblib)", type=["pkl", "joblib"], key="upload_model")

st.write("Optional: show more debug info for the classifier")
debug = st.checkbox("Show debug info/tracebacks", value=False, key="debug")

model = None
model_loaded_from = None

if uploaded_model is not None:
    # Save uploaded model to a temp file and load
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_model.name)[1])
    tmp.write(uploaded_model.getvalue())
    tmp.flush()
    tmp.close()
    model = load_model_from_bytes(open(tmp.name, "rb").read())
    model_loaded_from = f"uploaded: {uploaded_model.name}"
    # note: we don't remove the tmp right away so cached loader can access path if needed

else:
    # Try to load the model from the path specified
    if os.path.exists(model_from_repo):
        model = load_model_from_path(model_from_repo)
        model_loaded_from = f"path: {model_from_repo}"
    else:
        model = None
        model_loaded_from = f"path not found: {model_from_repo}"

if st.button("Classify email", key="classify_button"):
    if model is None:
        st.error(f"Model not loaded. {model_loaded_from}")
    else:
        if not email_text or email_text.strip() == "":
            st.warning("Paste an email to classify.")
        else:
            try:
                result = classify_with_model(model, preprocess_text(email_text))
                if "error" in result:
                    st.error("Classifier error: " + result.get("error", "Unknown error"))
                    if debug and "trace" in result:
                        st.code(result["trace"])
                else:
                    st.write("Predicted label:", result.get("label"))
                    if result.get("confidence") is not None:
                        st.write(f"Confidence: {result['confidence']:.2%}")
                    if debug:
                        st.write("Model type:", type(model))
                        st.write("Model attributes:", [a for a in dir(model) if not a.startswith("_")][:40])
            except Exception as e:
                st.exception(e)

st.markdown("---")
st.info("Notes: keep only one 'Generate response' button (above). Remove other occurrences of st.button('Generate response') from your code.")