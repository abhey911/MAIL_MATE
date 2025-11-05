import streamlit as st
import email
from email.header import decode_header

# Prefer package imports (works on deployed/packaged runs). Fall back to local imports
try:
    from MailBuddy.agents.email_agent import generate_email_response
    from MailBuddy.utils.email_sender import send_email
    from MailBuddy.utils.mailbuddy_triage import TriageTask
    from MailBuddy.utils.email_folder_manager import EmailFolderManager
    from MailBuddy.utils.contacts import load_contacts, save_contacts
except Exception:
    # Local/dev imports (when running from the project root)
    from agents.email_agent import generate_email_response
    from utils.email_sender import send_email
    from utils.mailbuddy_triage import TriageTask
    from utils.email_folder_manager import EmailFolderManager
    from utils.contacts import load_contacts, save_contacts

# Initialize session state for IMAP settings
if 'imap_configured' not in st.session_state:
    st.session_state.imap_configured = False
if 'folder_manager' not in st.session_state:
    st.session_state.folder_manager = None


st.set_page_config(page_title="Auto Email Responder", layout="wide")
st.title("📧 MailBuddy – Think Less, Send Smart")

# Helper: safe rerun (some Streamlit builds may not expose experimental_rerun)
def _safe_rerun():
    try:
        st.experimental_rerun()
    except Exception:
        # Fall back to setting a flag and asking the user to refresh
        st.session_state["_needs_refresh"] = True

if st.session_state.get("_needs_refresh"):
    st.info("Changes saved. Please refresh the page to see updates.")

# IMAP Settings Section
with st.expander("📬 Email Server Settings"):
    st.markdown("""
    **Gmail Setup Instructions:**
    1. Use your Gmail address
    2. For password, use an [App Password](https://myaccount.google.com/apppasswords)
    3. Server is pre-filled for Gmail
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        email_address = st.text_input("Email Address", key="imap_email", placeholder="your.email@gmail.com")
        imap_password = st.text_input("App Password", type="password", key="imap_password", 
                                    help="Use App Password from Gmail security settings")
    with col2:
        imap_server = st.text_input("IMAP Server", value="imap.gmail.com", key="imap_server")
        imap_port = st.number_input("IMAP Port", value=993, key="imap_port")
    
    if st.button("Configure Email Server"):
        if not email_address or not imap_password:
            st.warning("Please provide both email and password.")
        else:
            folder_manager = EmailFolderManager(
                email_address=email_address,
                password=imap_password,
                imap_server=imap_server,
                imap_port=imap_port
            )
            
            # Test connection and create folders
            if folder_manager.connect():
                st.success("Successfully connected to email server!")
                if folder_manager.ensure_folders_exist():
                    st.success("Email folders configured successfully!")
                    st.session_state.folder_manager = folder_manager
                    st.session_state.imap_configured = True
                folder_manager.disconnect()


subject_text = ""
sender_text = st.text_input("Sender Email Address")
email_text = st.text_area("Paste the email content you received:", height=300)
# Optional important info to include in the generated reply
important_info = st.text_area("Important info to include in reply (optional)", height=80)

# Add folder view if connected
if st.session_state.folder_manager:
    with st.expander("📁 Folder View", expanded=True):
        folder_manager = st.session_state.folder_manager
        try:
            if folder_manager.connect():
                st.markdown("### 📁 Mail Folders")
                
                # Get folder names from the mapping
                folder_names = ["INBOX"] + [
                    folder for folder in folder_manager.DEFAULT_FOLDER_MAPPING.values()
                    if folder.upper() != "INBOX"
                ]
                
                # Create folder labels with emojis
                folder_labels = {
                    "INBOX": "📥 Inbox",
                    "Urgent": "⚡ Urgent",
                    "Important": "🔔 Important",
                    "Newsletters": "📰 Newsletters",
                    "Receipts": "🧾 Receipts",
                    "Promotions": "🎯 Promotions",
                    "Archive": "📁 Archive"
                }
                
                # Create tabs for available folders
                tab_labels = [folder_labels.get(folder, f"📁 {folder}") for folder in folder_names]
                folder_tabs = st.tabs(tab_labels)
                
                # Display contents of each folder
                for tab, folder in zip(folder_tabs, folder_names):
                    with tab:
                        try:
                            emails = folder_manager.search_emails(folder=folder, limit=5)
                            if emails:
                                st.write(f"Recent emails in {folder}:")
                                for _, subject, sender in emails:
                                    st.markdown(f"- **{subject}** from {sender}")
                            else:
                                st.info(f"No recent emails in {folder}")
                        except Exception as e:
                            st.error(f"Error accessing folder {folder}: {str(e)}")
                
                folder_manager.disconnect()
        except Exception as e:
            st.error(f"Error connecting to email server: {str(e)}")
            if folder_manager:
                folder_manager.disconnect()

# Known contacts removed from UI (managed in code or config). Use empty list by default.
# Load known contacts from local storage (user-managed). Falls back to empty list.
known_contacts = load_contacts()

# Manage known contacts in UI
with st.expander("👥 Manage Known Contacts", expanded=False):
    col_a, col_b = st.columns([3, 1])
    with col_a:
        new_contact = st.text_input("Add contact email", key="new_contact_input")
    with col_b:
        if st.button("Add", key="add_contact_btn"):
            if new_contact:
                contact = new_contact.strip().lower()
                if contact and contact not in known_contacts:
                    known_contacts.append(contact)
                    save_contacts(known_contacts)
                    st.success(f"Added {contact}")
                    _safe_rerun()
                else:
                    st.info("Contact already present or empty")

    # Show existing contacts with remove buttons
    if known_contacts:
        for i, c in enumerate(list(known_contacts)):
            ccol1, ccol2 = st.columns([8,1])
            ccol1.write(c)
            if ccol2.button("Remove", key=f"rm_{i}"):
                known_contacts.pop(i)
                save_contacts(known_contacts)
                st.success(f"Removed {c}")
                _safe_rerun()

# Tone selector remains for response style
tone = st.selectbox("Select response tone", ["Professional", "Friendly", "Apologetic", "Persuasive"])

# Triage UI
st.markdown("## 📋 Email Triage")
triage_task = TriageTask(known_contacts=known_contacts)

# Show recent emails if IMAP is configured
if st.session_state.imap_configured and st.session_state.folder_manager:
    with st.expander("📥 Recent Emails"):
        folder_manager = st.session_state.folder_manager
        if folder_manager.connect():
            recent_emails = folder_manager.search_emails(folder="INBOX", limit=5)
            if recent_emails:
                selected_email = st.selectbox(
                    "Select an email to triage:",
                    options=recent_emails,
                    format_func=lambda x: f"{x[1]} - From: {x[2]}"
                )
                if selected_email:
                    subject_text = selected_email[1]
                    sender_text = selected_email[2]
            folder_manager.disconnect()

col1, col2 = st.columns([2, 1])
with col1:
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
            
            # Show move action if IMAP configured
            if st.session_state.imap_configured:
                target_folder = st.session_state.folder_manager.get_folder_for_category(triage_result.category)
                if st.button(f"📁 Move to {target_folder}"):
                    folder_manager = st.session_state.folder_manager
                    if folder_manager.connect():
                        if hasattr(st.session_state, 'selected_email') and st.session_state.selected_email:
                            msg_id = st.session_state.selected_email[0]
                            if folder_manager.move_email(msg_id, "INBOX", target_folder):
                                st.success(f"Moved email to {target_folder}")
                            folder_manager.disconnect()

with col2:
    if st.session_state.imap_configured:
        st.markdown("### 📁 Folders")
        folder_manager = st.session_state.folder_manager
        if folder_manager:
            for category, folder in folder_manager.DEFAULT_FOLDER_MAPPING.items():
                st.write(f"**{category}:** {folder}")

## Generate & Edit Reply
st.markdown("---")
if st.button("Generate Reply"):
    if not sender_text:
        st.warning("Please enter the sender's email address (used as recipient for the reply).")
    else:
        with st.spinner("Generating reply..."):
            # Pass important_info into the generator so it can be included
            generated = generate_email_response(email_text, tone, important_info=important_info)
            # Store in session state for editing/sending
            st.session_state['generated_reply'] = generated

# If we have a generated reply, show an editable field and a Send button
if st.session_state.get('generated_reply'):
    st.subheader("✉️ Generated Reply (editable)")
    edited_reply = st.text_area("Edit the reply before sending:", value=st.session_state.get('generated_reply',''), height=200)
    if st.button("Send Reply"):
        with st.spinner("Sending email..."):
            send_status = send_email(sender_text, edited_reply)
            if send_status:
                st.success(f"Email sent successfully to {sender_text}")
                # Clear generated reply after send
                st.session_state.pop('generated_reply', None)
            else:
                st.error("Failed to send the email.")