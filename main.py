import json
import sys
from pathlib import Path

from core.email_processor import process_email
from utils.helpers import print_banner, print_section


def load_inbox(file_path: str) -> list[dict]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Inbox file not found: {file_path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Inbox file must contain a JSON list of email objects.")

    return data


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python main.py data/sample_inbox.json")
        sys.exit(1)

    inbox_file = sys.argv[1]

    try:
        emails = load_inbox(inbox_file)
    except Exception as e:
        print(f"Error loading inbox: {e}")
        sys.exit(1)

    print_banner("Inbox-to-Task Operator")
    print(f"Loaded {len(emails)} email(s) from {inbox_file}")

    results = []

    for index, email in enumerate(emails, start=1):
        print_section(f"Processing Email {index}")
        try:
            result = process_email(email)
            results.append(result)
        except Exception as e:
            print(f"Failed to process email {index}: {e}")
            results.append(
                {
                    "email_id": email.get("id", f"unknown-{index}"),
                    "status": "failed",
                    "error": str(e),
                }
            )

    print_section("Run Summary")
    for result in results:
        email_id = result.get("email_id", "unknown")
        status = result.get("status", "completed")
        mode = result.get("mode", "N/A")
        print(f"- Email {email_id}: status={status}, mode={mode}")


if __name__ == "__main__":
    main()