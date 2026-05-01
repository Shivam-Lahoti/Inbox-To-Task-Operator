import json
from pathlib import Path
from typing import Dict, Optional


TONE_FILE = Path("data/tone_memory.json")


def load_tone_memory() -> Dict:
    """Load tone memory from file"""
    if not TONE_FILE.exists():
        return {}
    
    try:
        with open(TONE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading tone memory: {e}")
        return {}


def get_tone_profile(person_name: str) -> Dict:
    """Get tone profile for a specific person"""
    memory = load_tone_memory()
    
    # Check if we have learned tone for this person
    if person_name in memory:
        return memory[person_name]
    
    # Default tone profile
    return {
        "style": "concise, professional, warm",
        "avoid": "long paragraphs, sounding desperate, overexplaining",
        "examples": []
    }


def save_tone_edit(person_name: str, original_draft: str, edited_draft: str):
    """Save user's edit as a learning signal"""
    memory = load_tone_memory()
    
    if person_name not in memory:
        memory[person_name] = {
            "style": "learned from edits",
            "avoid": "",
            "examples": []
        }
    
    memory[person_name]["examples"].append({
        "original": original_draft,
        "edited": edited_draft
    })
    
    # Keep only last 5 examples
    memory[person_name]["examples"] = memory[person_name]["examples"][-5:]
    
    TONE_FILE.parent.mkdir(exist_ok=True)
    
    with open(TONE_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)
    
    print(f"Saved tone learning for {person_name}")