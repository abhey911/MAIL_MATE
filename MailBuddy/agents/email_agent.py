import os
import streamlit as st
import google.generativeai as genai

def _generate_fallback_response(email_text: str, tone: str, important_info: str | None = None) -> str:
    """Generate a basic fallback response when the AI model fails."""
    greeting = "Thank you for your email."
    
    tone_phrases = {
        "Professional": "I appreciate you reaching out.",
        "Friendly": "It's great to hear from you!",
        "Casual": "Thanks for getting in touch!",
        "Formal": "I acknowledge receipt of your message.",
    }
    
    tone_phrase = tone_phrases.get(tone.title(), tone_phrases["Professional"])
    
    response = f"{greeting} {tone_phrase}\n\n"
    response += "I am reviewing your message and will provide a detailed response soon.\n\n"
    
    if important_info:
        response += f"Please note: {important_info}\n\n"
    
    response += "Best regards,\n[Your name]"
    
    return response


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


def classify_email(email_text):
    """Classify the email to determine its type and suggested response tone."""
    if not email_text.strip():
        return None, None

    client = _get_gemini_client()
    if client is None:
        return None, None

    try:
        model = client.GenerativeModel('gemini-2.5-flash')
        prompt = f"""Analyze this email and provide two pieces of information:
1. Email Type (choose one): Urgent, Important, Newsletter, Receipt, Promotion, General
2. Best Tone (choose one): Professional, Friendly, Casual, Formal

Email content:
{email_text}

Return ONLY these two words separated by a comma, like: "Type,Tone"
"""
        response = model.generate_content(prompt)
        if response.text and response.text.strip():
            email_type, tone = response.text.strip().split(',')
            return email_type.strip(), tone.strip()
        return None, None
    except Exception:
        return None, None

def generate_email_response(email_text, tone, important_info: str | None = None):
    """Generate a reply using the Google Gemini API.
    
    If the API key is not configured, returns a helpful error string instead of raising at import time.
    """
    if not email_text.strip():
        return "Error: Please provide the email content to respond to."

    client = _get_gemini_client()
    if client is None:
        return (
            "Error: Google API key not configured.\n"
            "Set GOOGLE_API_KEY in `.streamlit/secrets.toml` or set the GOOGLE_API_KEY environment variable."
        )

    try:
        model = client.GenerativeModel('gemini-2.5-flash')

        # Build the prompt with specific instructions for handling important info
        prompt = f"""Write a reply to the following email using a {tone.lower()} tone. Make sure the response is professional and contextually appropriate.

Email content to respond to:
{email_text}

Instructions:
1. Use a {tone.lower()} tone throughout the response
2. Ensure the response is clear and concise
3. Address all points from the original email
4. Include an appropriate greeting and closing
5. Format the response with proper line breaks between paragraphs
"""
        if important_info:
            prompt += f"\nIMPORTANT: Incorporate this information naturally into the response:\n{important_info}\n"

        response = model.generate_content(prompt)
        if response.text and response.text.strip():
            return response.text.strip()

        # Fallback if response is empty but no error occurred
        return _generate_fallback_response(email_text, tone, important_info)

    except Exception as e:
        st.error(f"Error during response generation: {str(e)}")
        return _generate_fallback_response(email_text, tone, important_info)