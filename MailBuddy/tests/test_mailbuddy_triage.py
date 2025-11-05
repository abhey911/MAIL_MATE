import pytest

from MailBuddy.utils.mailbuddy_triage import TriageTask, EmailTriageResult


def test_newsletter_detection():
    task = TriageTask()
    email = {
        "subject": "Weekly Update: Latest Issue",
        "body": "Hello! In this weekly update we share news. To stop receiving this, click unsubscribe.",
        "sender": "newsletter@example.com",
    }
    result = task.run(email)
    assert isinstance(result, EmailTriageResult)
    assert result.category == "NEWSLETTER"
    assert result.action == "MOVE_TO_FOLDER: Newsletters"


def test_otp_receipt_detection_subject():
    task = TriageTask()
    email = {
        "subject": "Your OTP code: 123456",
        "body": "Use this code to verify your account.",
        "sender": "no-reply@service.com",
    }
    result = task.run(email)
    assert result.category == "OTP_RECEIPT"
    assert result.action == "MOVE_TO_FOLDER: Receipts"


def test_receipt_detection_body():
    task = TriageTask()
    email = {
        "subject": "Order Confirmation",
        "body": "This is your receipt for order #98765. Invoice attached.",
        "sender": "orders@shop.com",
    }
    result = task.run(email)
    assert result.category == "OTP_RECEIPT"
    assert result.action == "MOVE_TO_FOLDER: Receipts"


def test_promotional_detection():
    task = TriageTask()
    email = {
        "subject": "Limited time offer — 50% discount!",
        "body": "Buy now and save. Promo code inside.",
        "sender": "deals@store.com",
    }
    result = task.run(email)
    assert result.category == "PROMOTIONAL"
    assert result.action == "MOVE_TO_FOLDER: Promotions"


def test_urgent_from_known_contact():
    task = TriageTask(known_contacts=["boss@example.com"]) 
    email = {
        "subject": "Urgent: please review ASAP",
        "body": "Can you get this done immediately?",
        "sender": "boss@example.com",
    }
    result = task.run(email)
    assert result.category in ("URGENT", "IMPORTANT")
    # For known contact + urgency we expect URGENT
    assert result.action == "FLAG_PRIORITY: High"


def test_other_default():
    task = TriageTask()
    email = {
        "subject": "Hello there",
        "body": "Just wanted to say hi and check in.",
        "sender": "friend@example.com",
    }
    result = task.run(email)
    assert result.category == "OTHER"
    assert result.action == "MOVE_TO_FOLDER: Inbox"
