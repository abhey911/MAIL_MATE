"""MailBuddy triage module

Provides:
- EmailTriageResult (Pydantic) structured output
- Email input model
- TriageAgent (optional CrewAI integration with rule-based fallback)
- TriageTask wrapper to run the agent on an Email dict

Save as `MailMate/utils/mailbuddy_triage.py` and import in your Streamlit app.
"""
from typing import Literal, Optional, Dict, List
from pydantic import BaseModel, Field, ValidationError
import re


# -------------------------
# 1) Pydantic Output Model
# -------------------------
class EmailTriageResult(BaseModel):
    """
    Structured result returned by the classification agent.
    """
    category: Literal["URGENT", "IMPORTANT", "NEWSLETTER", "PROMOTIONAL", "OTP_RECEIPT", "OTHER"] = Field(
        ..., description="One of URGENT, IMPORTANT, NEWSLETTER, PROMOTIONAL, OTP_RECEIPT, OTHER"
    )
    action: str = Field(..., description="Instruction for the next agent, e.g. 'MOVE_TO_FOLDER: Receipts' or 'FLAG_PRIORITY: High'")
    justification: str = Field(..., description="One-sentence explanation of the classification decision")


# -------------------------
# Email input model
# -------------------------
class Email(BaseModel):
    subject: str
    body: str
    sender: str


# -------------------------
# 2) TriageAgent
# -------------------------
class TriageAgent:
    """
    TriageAgent: attempts to use CrewAI if available; otherwise falls back to deterministic rules.

    Role: 'Email Inbox Triage Specialist'
    Goal: 'Analyze the email subject and body to classify its category and determine the best automation action to achieve Inbox Zero.'
    Backstory: 'An expert system in digital communication triage, specializing in accurately identifying low-value and high-priority emails.'
    """

    def __init__(self, known_contacts: Optional[List[str]] = None):
        # known_contacts can be used to identify URGENT/IMPORTANT messages
        self.known_contacts = [c.lower() for c in (known_contacts or [])]

        # try to import a hypothetical CrewAI integration
        try:
            import crewai  # type: ignore
            self.crewai = crewai
        except Exception:
            self.crewai = None

    def analyze(self, email: Email) -> EmailTriageResult:
        """
        Return an EmailTriageResult for the provided Email.
        If CrewAI is available, this method will attempt to use it; otherwise it uses local rules.
        """
        if self.crewai:
            try:
                return self._analyze_with_crewai(email)
            except Exception as e:
                # fallback on any failure
                print(f"[TriageAgent] CrewAI call failed, falling back to rule-based classifier: {e}")

        return self._rule_based_analyze(email)

    def _analyze_with_crewai(self, email: Email) -> EmailTriageResult:
        """
        Hypothetical CrewAI usage:
        - Send a precise instruction/prompt that requires the model to return JSON matching EmailTriageResult.
        - Parse the JSON into EmailTriageResult.
        NOTE: This code depends on your CrewAI SDK; adapt as necessary.
        """
        # Example pseudo-code - adapt to your actual CrewAI SDK:
        prompt = f"""
You are an Email Inbox Triage Specialist.
Your output must be strictly JSON matching this schema:
{{"category": "...", "action": "...", "justification": "..."}}.

Criteria:
- NEWSLETTER: contains 'unsubscribe', 'weekly update', or 'latest issue'. Action: MOVE_TO_FOLDER: Newsletters
- OTP_RECEIPT: subject contains 'OTP', 'receipt', 'invoice', or verification code text. Action: MOVE_TO_FOLDER: Receipts
- URGENT/IMPORTANT: from a known contact and includes high-urgency language. Action: FLAG_PRIORITY: High
- PROMOTIONAL: contains promotional keywords like 'sale', 'offer', 'discount'. Action: MOVE_TO_FOLDER: Promotions
- OTHER: when none of the above match.

Email subject:
{email.subject}

Email body:
{email.body}

Sender:
{email.sender}

Respond with a single JSON object.
"""
        # PSEUDO: the actual call will depend on your crewai library
        response_text = self.crewai.run_prompt(prompt)  # <- replace with real call
        # Parse JSON
        import json
        parsed = json.loads(response_text)
        return EmailTriageResult(**parsed)

    # -------------------------
    # Rule-based fallback logic
    # -------------------------
    def _rule_based_analyze(self, email: Email) -> EmailTriageResult:
        subject = (email.subject or "").lower()
        body = (email.body or "").lower()
        sender = (email.sender or "").lower()

        # Helper matchers
        def contains_any(text: str, keywords: List[str]) -> bool:
            return any(k in text for k in keywords)

        # Low-value categories: NEWSLETTER
        newsletter_keywords = ["unsubscribe", "weekly update", "latest issue", "newsletter"]
        if contains_any(subject, newsletter_keywords) or contains_any(body, newsletter_keywords):
            return EmailTriageResult(
                category="NEWSLETTER",
                action="MOVE_TO_FOLDER: Newsletters",
                justification="Message contains newsletter indicators like 'unsubscribe' or 'weekly update'."
            )

        # OTP / Receipt
        otp_keywords = ["otp", "one time password", "verification code"]
        receipt_keywords = ["receipt", "invoice", "order receipt", "payment receipt"]
        # check subject first
        if contains_any(subject, otp_keywords + receipt_keywords) or contains_any(body, otp_keywords + receipt_keywords):
            return EmailTriageResult(
                category="OTP_RECEIPT",
                action="MOVE_TO_FOLDER: Receipts",
                justification="Subject or body indicates a receipt or verification/OTP (e.g., 'receipt', 'invoice', or 'otp')."
            )

        # Promotional
        promotional_keywords = ["sale", "offer", "discount", "buy now", "limited time", "promo", "promotional"]
        if contains_any(subject, promotional_keywords) or contains_any(body, promotional_keywords):
            return EmailTriageResult(
                category="PROMOTIONAL",
                action="MOVE_TO_FOLDER: Promotions",
                justification="Contains promotional language such as 'sale', 'offer', or 'discount'."
            )

        # URGENT / IMPORTANT
        urgency_keywords = ["urgent", "asap", "immediately", "important", "action required", "deadline", "respond immediately"]
        is_known_contact = any(k in sender for k in self.known_contacts)
        has_urgency = contains_any(subject + " " + body, urgency_keywords)

        if is_known_contact and has_urgency:
            return EmailTriageResult(
                category="URGENT",
                action="FLAG_PRIORITY: High",
                justification="From a known contact and contains high-urgency language such as 'urgent' or 'ASAP'."
            )
        if is_known_contact:
            # known contact but no urgent language -> IMPORTANT
            return EmailTriageResult(
                category="IMPORTANT",
                action="FLAG_PRIORITY: High",
                justification="From a known contact; marked important to ensure a timely response."
            )
        if has_urgency:
            # urgent language but not known contact -> IMPORTANT (or URGENT depending on your policy)
            return EmailTriageResult(
                category="IMPORTANT",
                action="FLAG_PRIORITY: High",
                justification="Contains urgent language; flagged for prompt attention."
            )

        # Default fallback
        return EmailTriageResult(
            category="OTHER",
            action="MOVE_TO_FOLDER: Inbox",
            justification="No matching criteria for special categories; leave in Inbox for manual review."
        )


# -------------------------
# 3) TriageTask
# -------------------------
class TriageTask:
    """
    Task that accepts an Email dict (subject, body, sender) and returns EmailTriageResult.

    The task description explicitly instructs the criteria:
      - NEWSLETTER: If the email contains words like "unsubscribe", "weekly update", or "latest issue".
                  Action: MOVE_TO_FOLDER: Newsletters
      - OTP_RECEIPT: If the subject contains "OTP", "receipt", "invoice", or a verification code format.
                     Action: MOVE_TO_FOLDER: Receipts
      - URGENT/IMPORTANT: If the email is from a known contact and uses high-urgency language.
                          Action: FLAG_PRIORITY: High
      - PROMOTIONAL: promotional language; Action: MOVE_TO_FOLDER: Promotions
      - OTHER: fallback
    """

    def __init__(self, known_contacts: Optional[List[str]] = None):
        self.agent = TriageAgent(known_contacts=known_contacts)

    def run(self, email_dict: Dict[str, str]) -> EmailTriageResult:
        """
        Accepts a dict with keys 'subject', 'body', 'sender' (strings).
        Returns EmailTriageResult.
        """
        try:
            email = Email(**email_dict)
        except ValidationError as e:
            raise ValueError(f"Invalid email input: {e}")

        result = self.agent.analyze(email)
        return result


# -------------------------
# 4) Example Input & Demo
# -------------------------
if __name__ == "__main__":
    # Example: a receipt email (sample input)
    sample_email = {
        "subject": "Your Order Receipt #12345",
        "body": "Thank you for your purchase! This email is your receipt. Total: $39.99. If you have questions, reply to this email.",
        "sender": "orders@shop-example.com"
    }

    # Example known contacts (e.g., professor or supervisor email addresses or domains)
    known_contacts = ["boss@example.com", "professor@university.edu", "supervisor@work.com"]

    task = TriageTask(known_contacts=known_contacts)
    triage_result = task.run(sample_email)

    print("Triage result (object):", triage_result)
    print("Triage result (json):", triage_result.json(indent=2))
