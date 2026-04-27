from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.source_loader import load_all_sources
from core.normalizer import normalize_all_sources, normalize_email
from core.person_resolution import resolve_person
from core.chunker import build_chunks
from core.retriever import retrieve_context
from core.context_aggregator import aggregate_context
from core.tone_profile import get_tone_profile
from core.reply_generator import generate_reply
from core.feedback_learning import learn_from_user_edit


console = Console()


def build_incoming_message():
    raw_email = {
        "email_id": "incoming_email_001",
        "from_name": "Ananya Sharma",
        "from_email": "ananya@healthai.com",
        "to_email": "shivam@example.com",
        "subject": "Intro Call Tomorrow",
        "timestamp": "2026-04-22T12:30:00",
        "body": "Hi Shivam, are you free tomorrow afternoon for a quick call to discuss the Applied AI Engineer role?"
    }

    return normalize_email(raw_email)


def print_resolved_people(resolved_matches):
    table = Table(title="Person Resolution Results")
    table.add_column("Source")
    table.add_column("Name")
    table.add_column("Email")
    table.add_column("Phone")
    table.add_column("Handle")
    table.add_column("Score")

    for msg, score in resolved_matches:
        table.add_row(
            msg.source,
            msg.person_name,
            msg.email or "-",
            msg.phone or "-",
            msg.handle or "-",
            str(score)
        )

    console.print(table)


def print_rag_results(rag_results):
    table = Table(title="RAG Retrieved Context")
    table.add_column("Source")
    table.add_column("Timestamp")
    table.add_column("Score")
    table.add_column("Text")

    for item in rag_results:
        table.add_row(
            item["source"],
            item["timestamp"],
            str(item["rag_score"]),
            item["text"][:90]
        )

    console.print(table)


def run_operator():
    console.print(
        Panel.fit(
            "Cross-Channel Relationship-Aware Reply Operator",
            style="bold cyan"
        )
    )

    raw_sources = load_all_sources()
    normalized_messages = normalize_all_sources(raw_sources)

    incoming_message = build_incoming_message()

    console.print("\n[bold]Incoming Message[/bold]")
    console.print(
        Panel(
            f"From: {incoming_message.person_name}\n"
            f"Source: {incoming_message.source}\n"
            f"Subject: {incoming_message.subject}\n\n"
            f"{incoming_message.text}"
        )
    )

    resolved_matches = resolve_person(
        incoming=incoming_message,
        all_messages=normalized_messages
    )

    print_resolved_people(resolved_matches)

    resolved_messages = [match[0] for match in resolved_matches]
    chunks = build_chunks(resolved_messages)

    rag_query = f"""
    {incoming_message.person_name}
    {incoming_message.subject}
    {incoming_message.text}
    """

    rag_results = retrieve_context(
        query=rag_query,
        chunks=chunks,
        top_k=5
    )

    print_rag_results(rag_results)

    aggregated_context = aggregate_context(
        incoming_message=incoming_message,
        resolved_matches=resolved_matches,
        rag_results=rag_results
    )

    tone_profile = get_tone_profile(incoming_message.person_name)

    draft_reply = generate_reply(
        incoming_message=incoming_message,
        aggregated_context=aggregated_context,
        tone_profile=tone_profile
    )

    console.print("\n[bold green]Generated Reply Draft[/bold green]")
    console.print(Panel(draft_reply, style="green"))

    console.print("\n[bold yellow]Human-in-the-loop Review[/bold yellow]")
    edited_reply = input(
        "Edit the reply and press Enter. Or press Enter directly to approve as-is:\n\n"
    )

    if edited_reply.strip():
        learned = learn_from_user_edit(
            person_name=incoming_message.person_name,
            original_draft=draft_reply,
            edited_draft=edited_reply
        )

        console.print("\n[bold green]Final Edited Reply[/bold green]")
        console.print(Panel(edited_reply, style="green"))

        if learned:
            console.print("[cyan]Saved edit as future tone-learning signal.[/cyan]")
    else:
        console.print("[green]Approved draft. MVP does not auto-send.[/green]")


if __name__ == "__main__":
    run_operator()