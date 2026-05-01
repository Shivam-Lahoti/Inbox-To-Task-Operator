import json
from pathlib import Path
from typing import List, Dict


DATA_DIR = Path("data")


def load_json_file(file_name: str) -> List[Dict]:
    """Load a JSON file from data directory"""
    file_path = DATA_DIR / file_name
    
    if not file_path.exists():
        print(f"{file_name} not found, returning empty list")
        return []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"Loaded {len(data)} messages from {file_name}")
            return data
    except Exception as e:
        print(f"Error loading {file_name}: {e}")
        return []


def load_all_sources() -> Dict[str, List[Dict]]:
    """Load all message sources"""
    return {
        "email": load_json_file("email_messages.json"),
        "linkedin": load_json_file("linkedin_messages.json"),
        "whatsapp": load_json_file("whatsapp_messages.json"),
        "sms": load_json_file("sms_messages.json")
    }


def load_test_cases() -> List[Dict]:
    """Load test cases for CLI demo"""
    return load_json_file("test_cases.json")