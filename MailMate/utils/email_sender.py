import os
import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(recipient, body):
    try:
        # Prefer st.secrets when available, fall back to environment variables for dev
        sender_email = None
        sender_password = None
        try:
            sender_email = st.secrets.get("SENDER_EMAIL")
            sender_password = st.secrets.get("EMAIL_PASSWORD")
        except Exception:
            sender_email = None
            sender_password = None

        sender_email = sender_email or os.environ.get("SENDER_EMAIL")
        sender_password = sender_password or os.environ.get("EMAIL_PASSWORD")

        smtp_server = None
        smtp_port = None
        try:
            smtp_server = st.secrets.get("SMTP_SERVER")
            smtp_port = st.secrets.get("SMTP_PORT")
        except Exception:
            smtp_server = None
            smtp_port = None

        smtp_server = smtp_server or os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(smtp_port or os.environ.get("SMTP_PORT", 587))

        if not sender_email or not sender_password:
            print("Email credentials not configured (SENDER_EMAIL, EMAIL_PASSWORD). Skipping send.")
            return False

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient
        message["Subject"] = "Response To Your Email"

        message.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)
        server.quit()
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False