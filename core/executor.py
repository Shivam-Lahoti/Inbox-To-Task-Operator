from utils.helpers import print_subsection


def execute_action(
    email: dict,
    summary: str,
    classification: dict,
    task: dict,
    mode: str,
    draft: str | None = None,
) -> str:
    """
    Execute the selected action path for an email.

    Returns a status string.
    """
    sender = email.get("from", "unknown")
    subject = email.get("subject", "No Subject")

    print_subsection(f"From: {sender}")
    print(f"Subject: {subject}")
    print(f"Summary: {summary}")
    print(f"Mode: {mode}")

    if mode == "AUTO":
        print("Action: Email automatically archived or marked as no-action.")
        return "auto_completed"

    if mode == "DRAFT":
        print("\nDraft Reply:")
        print("-" * 50)
        print(draft or "[No draft generated]")
        print("-" * 50)

        user_input = input("Approve and send? (y/n/edit): ").strip().lower()

        if user_input == "y":
            print("Draft approved and sent.")
            return "approved_and_sent"

        if user_input == "edit":
            print("\nEnter your edited reply below. Press Enter when done.")
            edited_reply = input("> ").strip()

            if edited_reply:
                print("\nEdited draft sent.")
                return "edited_and_sent"

            print("\nNo edit provided. Draft not sent.")
            return "draft_not_sent"

        print("Draft rejected.")
        return "draft_rejected"

    if mode == "ESCALATE":
        print("\nEscalation Required")
        print("-" * 50)
        print(f"Priority: {classification.get('priority')}")
        print(f"Intent: {classification.get('intent')}")
        print(f"Task: {task.get('action')}")
        print(f"Context: {task.get('context')}")
        print("\nSuggested Reply:")
        print(draft or "[No suggested reply generated]")
        print("-" * 50)
        print("This email requires human review before any action is taken.")
        return "escalated_to_human"

    print("Unknown mode. No action taken.")
    return "no_action_taken"