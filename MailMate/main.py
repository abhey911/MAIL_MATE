import streamlit as st
from agents.email_agent import generate_email_response
from utils.email_sender import send_email

try:
    # TriageTask lives in utils/mailbuddy_triage.py
    from utils.mailbuddy_triage import TriageTask
except Exception:
    # Fallback to package-style import if running as module
    from MailMate.utils.mailbuddy_triage import TriageTask


st.set_page_config(page_title="Auto Email Responder", layout="wide")
st.title("📧 MailMate – Think Less, Send Smart")

# Email metadata inputs
subject_text = st.text_input("Email Subject")
sender_text = st.text_input("Sender Email Address")
email_text = st.text_area("Paste the email content you received:", height=300)

# Known contacts (comma-separated) used to mark important/urgent
known_contacts_input = st.text_input("Known contacts (comma-separated)", value="boss@example.com")
known_contacts = [c.strip() for c in known_contacts_input.split(",") if c.strip()]

tone = st.selectbox("Select response tone", ["Professional", "Friendly", "Apologetic", "Persuasive"])
model_choice = st.selectbox("Select model", ["gemini-pro"], index=0, help="Using Google's Gemini Pro model for generating responses")

# Triage UI
st.markdown("## 📋 Email Triage")
triage_task = TriageTask(known_contacts=known_contacts)
if st.button("Classify Email"):
    if not subject_text and not email_text and not sender_text:
        st.warning("Please provide at least the subject, sender, or body to classify the email.")
    else:
        with st.spinner("Classifying email..."):
            triage_result = triage_task.run({
                "subject": subject_text or "",
                "body": email_text or "",
                "sender": sender_text or "",
            })
        st.success("Classification complete")
        st.write("**Category:**", triage_result.category)
        st.write("**Action:**", triage_result.action)
        st.write("**Justification:**", triage_result.justification)

# Generate & Send flow
st.markdown("---")
if st.button("Generate & Send Email"):
    if not sender_text:
        st.warning("Please enter the sender's email address (used as recipient for the reply).")
    else:
        with st.spinner("Generating and sending email..."):
            # Generate the response using the configured agent
            response = generate_email_response(email_text, tone, model_name=model_choice)
            send_status = send_email(sender_text, response)
            st.subheader("✉️ Response")
            st.markdown(response, unsafe_allow_html=True)
            if send_status:
                st.success(f"Email sent successfully to {sender_text}")
            else:
                st.error("Failed to send the email.")