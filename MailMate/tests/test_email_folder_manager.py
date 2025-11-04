"""Tests for email folder manager functionality."""
import pytest
from unittest.mock import MagicMock, patch
from MailMate.utils.email_folder_manager import EmailFolderManager
from MailMate.utils.mailbuddy_triage import TriageTask

def test_folder_mapping():
    """Test that folder mappings are correctly assigned."""
    manager = EmailFolderManager(
        email_address="test@example.com",
        password="dummy"
    )
    
    # Check default mappings
    assert manager.get_folder_for_category("URGENT") == "Urgent"
    assert manager.get_folder_for_category("NEWSLETTER") == "Newsletters"
    assert manager.get_folder_for_category("OTP_RECEIPT") == "Receipts"
    
    # Check custom mapping
    custom_mapping = {
        "URGENT": "High_Priority",
        "NEWSLETTER": "Updates",
        "OTHER": "General"
    }
    manager = EmailFolderManager(
        email_address="test@example.com",
        password="dummy",
        folder_mapping=custom_mapping
    )
    assert manager.get_folder_for_category("URGENT") == "High_Priority"
    assert manager.get_folder_for_category("NEWSLETTER") == "Updates"
    assert manager.get_folder_for_category("PROMOTIONAL") == "General"  # falls back to OTHER

def test_triage_integration():
    """Test that triage results map to correct folders."""
    triage = TriageTask(known_contacts=["boss@example.com"])
    manager = EmailFolderManager(
        email_address="test@example.com",
        password="dummy"
    )
    
    # Test urgent email from boss
    urgent_email = {
        "subject": "Urgent Review Needed",
        "body": "Please review this ASAP",
        "sender": "boss@example.com"
    }
    result = triage.run(urgent_email)
    target_folder = manager.get_folder_for_category(result.category)
    assert target_folder == "Urgent"  # Should go to Urgent folder
    
    # Test newsletter
    newsletter_email = {
        "subject": "Weekly Updates",
        "body": "Here are your weekly updates. Click here to unsubscribe.",
        "sender": "news@example.com"
    }
    result = triage.run(newsletter_email)
    target_folder = manager.get_folder_for_category(result.category)
    assert target_folder == "Newsletters"

@patch('imaplib.IMAP4_SSL')
def test_folder_creation(mock_imap):
    """Test IMAP folder creation with mocked connection."""
    # Setup mock
    mock_connection = MagicMock()
    mock_imap.return_value = mock_connection
    
    # Simulate existing folders response
    mock_connection.list.return_value = ('OK', [b'() "/" "INBOX"'])
    
    manager = EmailFolderManager(
        email_address="test@example.com",
        password="dummy"
    )
    
    # Connect and create folders
    assert manager.connect()
    assert manager.ensure_folders_exist()
    
    # Count number of non-INBOX folders that should be created
    expected_creates = sum(1 for f in manager.DEFAULT_FOLDER_MAPPING.values() if f.upper() != "INBOX")
    assert mock_connection.create.call_count == expected_creates
    
    # Verify each non-INBOX folder was created
    for folder in manager.DEFAULT_FOLDER_MAPPING.values():
        if folder.upper() != "INBOX":
            mock_connection.create.assert_any_call(folder)
        mock_connection.create.assert_any_call(folder)

@patch('imaplib.IMAP4_SSL')
def test_move_email(mock_imap):
    """Test email move operation with mocked IMAP."""
    # Setup mock
    mock_connection = MagicMock()
    mock_imap.return_value = mock_connection
    
    manager = EmailFolderManager(
        email_address="test@example.com",
        password="dummy"
    )
    
    # Test move operation
    assert manager.connect()
    result = manager.move_email("1", "INBOX", "Urgent")
    assert result is True
    
    # Verify IMAP operations
    mock_connection.select.assert_called_with("INBOX")
    mock_connection.copy.assert_called_with("1", "Urgent")
    mock_connection.store.assert_called_with("1", '+FLAGS', '\\Deleted')
    mock_connection.expunge.assert_called()