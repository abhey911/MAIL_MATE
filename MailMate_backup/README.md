# MailBuddy

Small Streamlit app that generates email replies using OpenAI and can send them via SMTP.

Quick start (local)
1. Create a Python 3.11+ virtual environment and activate it.
2. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

3. Add secrets for local development:

- Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in the values.
- Alternatively set environment variables `OPENAI_API_KEY`, `SENDER_EMAIL`, `EMAIL_PASSWORD`, and optionally `SMTP_SERVER`/`SMTP_PORT`.

4. Run the app:

```powershell
streamlit run main.py
```

Deployment to Streamlit Cloud
- Push this repo to GitHub. Create a Streamlit Community app and point it at the repository.
- In the Streamlit Cloud app settings, add the secrets (OPENAI_API_KEY, SENDER_EMAIL, EMAIL_PASSWORD, etc.) under "Secrets" — do not commit secrets to the repo.

Notes & suggestions
- The app uses the OpenAI SDK via `agents/email_agent.py`. The code provides environment-variable fallbacks.
- The app currently uses model `gpt-4`. If you don't have access to `gpt-4` on the platform you may need to switch to another available model (e.g., `gpt-4o-mini` or a GPT-3.5 alternative).
- Sending real email requires valid SMTP credentials. For testing, use a throwaway account or a local SMTP testing service.

Security
- Never commit `.streamlit/secrets.toml` to source control. Use the provided `.streamlit/secrets.toml.example` as a template.

If you want, I can also add a simple unit test and a GitHub Actions workflow for CI.
