from core.tone_profile import save_tone_edit


def learn_from_user_edit(
    person_name: str,
    original_draft: str,
    edited_draft: str
) -> bool:
    if not edited_draft.strip():
        return False

    if edited_draft.strip() == original_draft.strip():
        return False

    save_tone_edit(
        person_name=person_name,
        original_draft=original_draft,
        edited_draft=edited_draft
    )

    return True