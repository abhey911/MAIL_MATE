from pathlib import Path
from typing import List
import json

# Default path: MailBuddy/data/known_contacts.json
DEFAULT_PATH = Path(__file__).resolve().parents[1] / "data" / "known_contacts.json"


def load_contacts(path: Path = DEFAULT_PATH) -> List[str]:
    """Load known contacts from a JSON file. Returns list of lowercase emails."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return [str(e).strip().lower() for e in data if e]
            return []
    except Exception:
        return []


def save_contacts(contacts: List[str], path: Path = DEFAULT_PATH) -> None:
    """Save contacts (list of strings) to the JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([c.strip().lower() for c in contacts], f, indent=2)
