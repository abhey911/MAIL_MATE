"""Email folder management using IMAP.

This module provides EmailFolderManager for:
- Creating folders based on triage categories
- Moving emails to appropriate folders
- Managing IMAP connections and operations
"""
import imaplib
import email
from email.header import decode_header
from typing import Dict, Optional, List, Tuple
import streamlit as st


class EmailFolderManager:
    """Manages email folders and moving messages using IMAP."""

    # Default folder mapping for triage categories
    DEFAULT_FOLDER_MAPPING = {
        "URGENT": "Urgent",
        "IMPORTANT": "Important",
        "NEWSLETTER": "Newsletters",
        "PROMOTIONAL": "Promotions",
        "OTP_RECEIPT": "Receipts",
        "OTHER": "Archive"
    }

    def __init__(
        self,
        email_address: str,
        password: str,
        imap_server: str = "imap.gmail.com",
        imap_port: int = 993,
        folder_mapping: Optional[Dict[str, str]] = None,
        use_ssl: bool = True
    ):
        """Initialize with IMAP credentials and folder mapping.
        
        Args:
            email_address: Email address for IMAP login
            password: Password or app-specific password
            imap_server: IMAP server hostname
            imap_port: IMAP port (default 993 for SSL)
            folder_mapping: Custom mapping of triage categories to folder names
            use_ssl: Whether to use SSL for connection (recommended)
        """
        self.email = email_address
        self.password = password
        self.server = imap_server
        self.port = imap_port
        self.use_ssl = use_ssl
        self.folder_mapping = folder_mapping or self.DEFAULT_FOLDER_MAPPING
        self._imap = None

    def connect(self) -> bool:
        """Connect to the IMAP server.
        
        Returns:
            bool: True if connection successful
        """
        try:
            if self.use_ssl:
                self._imap = imaplib.IMAP4_SSL(self.server, self.port)
            else:
                self._imap = imaplib.IMAP4(self.server, self.port)
            
            self._imap.login(self.email, self.password)
            return True
        except Exception as e:
            st.error(f"Failed to connect to email server: {str(e)}")
            return False

    def disconnect(self):
        """Safely disconnect from IMAP server."""
        if self._imap:
            try:
                self._imap.logout()
            except:
                pass
            self._imap = None

    def ensure_folders_exist(self) -> bool:
        """Create folders for all triage categories if they don't exist.
        
        Returns:
            bool: True if all folders exist or were created
        """
        if not self._imap:
            if not self.connect():
                return False

        try:
            # List existing folders
            _, folders = self._imap.list()
            existing = set()
            for folder_info in folders:
                # Decode folder names which may use different encodings
                folder_info_str = folder_info.decode('utf-8')
                # Extract folder name (last quoted part)
                parts = folder_info_str.split('" "')
                if len(parts) > 1:
                    folder_name = parts[-1].strip('"')
                    existing.add(folder_name)

            # Create missing folders
            for category, folder in self.folder_mapping.items():
                if folder not in existing:
                    try:
                        self._imap.create(folder)
                        st.success(f"Created folder: {folder}")
                    except Exception as e:
                        st.error(f"Failed to create folder {folder}: {str(e)}")
                        return False
            return True
        except Exception as e:
            st.error(f"Error managing folders: {str(e)}")
            return False

    def move_email(self, message_id: str, source_folder: str, target_folder: str) -> bool:
        """Move an email from one folder to another.
        
        Args:
            message_id: The message ID or UID
            source_folder: Source folder name (e.g., "INBOX")
            target_folder: Target folder name from folder_mapping
            
        Returns:
            bool: True if move successful
        """
        if not self._imap:
            if not self.connect():
                return False

        try:
            # Select source folder
            self._imap.select(source_folder)
            
            # Copy to destination
            self._imap.copy(message_id, target_folder)
            
            # Mark original for deletion
            self._imap.store(message_id, '+FLAGS', '\\Deleted')
            
            # Expunge to remove deleted messages
            self._imap.expunge()
            
            return True
        except Exception as e:
            st.error(f"Failed to move email: {str(e)}")
            return False

    def get_folder_for_category(self, category: str) -> str:
        """Get the folder name for a triage category.
        
        Args:
            category: One of the triage categories (URGENT, IMPORTANT, etc.)
            
        Returns:
            str: Folder name from mapping
        """
        return self.folder_mapping.get(category, self.folder_mapping["OTHER"])

    def search_emails(
        self,
        criteria: str = "ALL",
        folder: str = "INBOX",
        limit: int = 10
    ) -> List[Tuple[str, str, str]]:
        """Search for emails matching criteria in a folder.
        
        Args:
            criteria: IMAP search criteria (default "ALL")
            folder: Folder to search (default "INBOX")
            limit: Max number of results
            
        Returns:
            List of (message_id, subject, sender) tuples
        """
        if not self._imap:
            if not self.connect():
                return []

        try:
            self._imap.select(folder)
            _, messages = self._imap.search(None, criteria)
            
            results = []
            for num in messages[0].split()[:limit]:
                _, msg_data = self._imap.fetch(num, '(RFC822)')
                email_body = msg_data[0][1]
                message = email.message_from_bytes(email_body)
                
                # Decode subject
                subject = decode_header(message["subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                
                # Get sender
                sender = message["from"]
                
                results.append((num.decode(), subject, sender))
            
            return results
        except Exception as e:
            st.error(f"Failed to search emails: {str(e)}")
            return []

    def __enter__(self):
        """Context manager support."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure disconnection."""
        self.disconnect()