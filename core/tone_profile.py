import json
from pathlib import Path


MEMORY_PATH = Path("data/tone_memory.json")


def load_tone_memory() -> dict:
    if not MEMORY_PATH.exists():
        return {
            "default": {
                "style": "concise, professional, warm",
                "avoid": "long paragraphs, sounding desperate, overexplaining",
                "examples": []
            }
        }

    with open(MEMORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_tone_profile(person_name: str) -> dict:
    memory = load_tone_memory()

    if person_name in memory:
        return memory[person_name]

    return memory["default"]


def save_tone_edit(person_name: str, original_draft: str, edited_draft: str):
    memory = load_tone_memory()

    if person_name not in memory:
        memory[person_name] = {
            "style": "concise, professional, warm",
            "avoid": "long paragraphs, sounding desperate, overexplaining",
            "examples": []
        }

    memory[person_name]["examples"].append({
        "original_draft": original_draft,
        "edited_draft": edited_draft
    })

    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)