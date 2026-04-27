import json
from pathlib import Path


DATA_DIR = Path("data")


def load_json_file(file_name: str) -> list[dict]:
    path = DATA_DIR / file_name

    if not path.exists():
        raise FileNotFoundError(f"Missing data file: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_sources() -> dict[str, list[dict]]:
    return {
        "email": load_json_file("email_messages.json"),
        "linkedin": load_json_file("linkedin_messages.json"),
        "whatsapp": load_json_file("whatsapp_messages.json"),
        "sms": load_json_file("sms_messages.json")
    }