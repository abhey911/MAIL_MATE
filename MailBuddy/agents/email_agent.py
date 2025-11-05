import os
import streamlit as st
import google.generativeai as genai


def _get_gemini_client():
    """Configure and return Gemini API client using st.secrets or environment variable fallback.
    Returns None if no API key is configured.
    """
    api_key = None
    try:
        api_key = st.secrets.get("GOOGLE_API_KEY")
    except Exception:
        api_key = None

    if not api_key:
        api_key = os.environ.get("GOOGLE_API_KEY")

    if not api_key:
        return None
    
   
    genai.configure(api_key=api_key)
    return genai


def generate_email_response(email_text, tone, important_info: str | None = None, model_name=None):
    """Generate a reply using the Google Gemini API.

    If the API key is not configured, returns a helpful error string instead of raising at import time.
    """
    client = _get_gemini_client()
    if client is None:
        return (
            "Error: Google API key not configured.\n"
            "Set GOOGLE_API_KEY in `.streamlit/secrets.toml` or set the GOOGLE_API_KEY environment variable."
        )

    
    model = client.GenerativeModel('gemini-2.5-flash')

    # Build the prompt. If `important_info` is provided, ask the model to include it.
    prompt = f"""Write a reply to the following email using a {tone.lower()} tone. Make sure the response is professional and contextually appropriate.

Email content to respond to:
{email_text}

Instructions:
1. Use a {tone.lower()} tone throughout the response
2. Ensure the response is clear and concise
3. Address all points from the original email
4. Include an appropriate greeting and closing
"""
    if important_info:
        prompt += f"\nAdditional important information to include in the reply:\n{important_info}\n"

    try:
        response = model.generate_content(prompt)
        if response.text:
            return response.text
        return "Error: Unable to generate response. Please try again."
    except Exception as e:
        return f"Error generating response: {str(e)}"
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        # Guard against unexpected response shapes
        return getattr(response.choices[0].message, "content", "").strip()
    except Exception as e:
        return f"Error generating response: {e}"