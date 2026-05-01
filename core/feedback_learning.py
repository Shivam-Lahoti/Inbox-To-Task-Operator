from core.tone_profile import save_tone_edit


def learn_from_user_edit(person_name: str, original_draft: str, edited_draft: str):
    """Learn from user's edits to improve future replies"""
    
    if original_draft.strip() == edited_draft.strip():
        print("ℹ️  No changes detected, skipping learning")
        return
    
    save_tone_edit(person_name, original_draft, edited_draft)
    print(f"✅ Learned from your edit for {person_name}")