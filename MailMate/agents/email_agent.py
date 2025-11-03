import os
import streamlit as st
import openai


def _get_openai_client():
    """Return an OpenAI client using st.secrets or environment variable fallback.
    Returns None if no API key is configured.
    """
    api_key = None
    try:
        api_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        api_key = None

    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        return None

    return openai.OpenAI(api_key=api_key)


def generate_email_response(email_text, tone, model_name=None):
    """Generate a reply using the OpenAI API.

    If the API key is not configured, returns a helpful error string instead of raising at import time.
    """
    client = _get_openai_client()
    if client is None:
        return (
            "Error: OpenAI API key not configured.\n"
            "Set OPENAI_API_KEY in `.streamlit/secrets.toml` or set the OPENAI_API_KEY environment variable."
        )

    # Determine which model to use: preference order -> explicit arg, st.secrets, env var, default free model
    if not model_name:
        try:
            model_name = st.secrets.get("OPENAI_MODEL")
        except Exception:
            model_name = None

    if not model_name:
        model_name = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")

    prompt = f"""
You are an AI assistant. Write a reply to the following email using a {tone.lower()} tone:

Email:
{email_text}

Reply:
"""
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        # Guard against unexpected response shapes
        return getattr(response.choices[0].message, "content", "").strip()
    except Exception as e:
        return f"Error generating response: {e}"