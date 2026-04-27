from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from core.logger import OperatorLogger
from core.source_loader import load_all_sources, load_test_cases
from core.normalizer import normalize_all_sources, normalize_email,normalize_incoming
from core.person_resolution import resolve_person
from core.chunker import build_chunks
from core.retriever import retrieve_context
from core.context_aggregator import aggregate_context
from core.tone_profile import get_tone_profile
from core.reply_generator import generate_reply
from core.feedback_learning import learn_from_user_edit


console = Console()


def select_test_case():
    test_cases = load_test_cases()

    console.print("\n[bold cyan]Available Test Cases[/bold cyan]")

    table = Table(title="Demo Scenarios")
    table.add_column("Option")
    table.add_column("Case ID")
    table.add_column("Description")

    for idx, case in enumerate(test_cases, start=1):
        table.add_row(
            str(idx),
            case["case_id"],
            case["description"]
        )

    console.print(table)

    choice = input("\nSelect test case number: ").strip()

    if not choice:
        return test_cases[0]

    index = int(choice) - 1

    if index < 0 or index >= len(test_cases):
        raise ValueError("Invalid test case selected")

    return test_cases[index]


def build_incoming_message():
    test_case = select_test_case()

    console.print(
        Panel(
            f"Case: {test_case['case_id']}\n"
            f"{test_case['description']}",
            title="Selected Test Case",
            style="cyan"
        )
    )

    return normalize_incoming(
        source=test_case["incoming_source"],
        raw=test_case["incoming"]
    )


def print_resolved_people(resolved_matches):
    table = Table(title="Person Resolution Results")
    table.add_column("Source")
    table.add_column("Name")
    table.add_column("Email")
    table.add_column("Phone")
    table.add_column("Handle")
    table.add_column("Company")
    table.add_column("Score")
    table.add_column("Reasons")

    for msg, score, reasons in resolved_matches:
        table.add_row(
            msg.source,
            msg.person_name,
            msg.email or "-",
            msg.phone or "-",
            msg.handle or "-",
            msg.company or "-",
            str(score),
            ", ".join(reasons)
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
    logger = OperatorLogger()

    console.print(
        Panel.fit(
            "Cross-Channel Relationship-Aware Reply Operator",
            style="bold cyan"
        )
    )

    logger.log(
        step="START",
        message="Operator started"
    )

    raw_sources = load_all_sources()

    logger.log(
        step="SOURCE_LOADING",
        message="Loaded raw messages from all connected mock sources",
        data={
            source: len(messages)
            for source, messages in raw_sources.items()
        }
    )

    normalized_messages = normalize_all_sources(raw_sources)

    logger.log(
        step="NORMALIZATION",
        message="Converted all source-specific records into common NormalizedMessage schema",
        data={
            "total_normalized_messages": len(normalized_messages),
            "sources": list(raw_sources.keys())
        }
    )

    incoming_message = build_incoming_message()

    logger.log(
        step="INCOMING_MESSAGE",
        message="Selected incoming message as current trigger",
        data={
            "source": incoming_message.source,
            "person_name": incoming_message.person_name,
            "email": incoming_message.email,
            "phone": incoming_message.phone,
            "handle": incoming_message.handle,
            "company": incoming_message.company,
            "subject": incoming_message.subject,
            "text": incoming_message.text
        }
    )

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

    logger.log(
        step="PERSON_RESOLUTION",
        message="Resolved likely same-person records across channels",
        data=[
            {
                "source": msg.source,
                "name": msg.person_name,
                "email": msg.email,
                "phone": msg.phone,
                "handle": msg.handle,
                "company": msg.company,
                "score": score,
                "reasons": reasons,
                "text_preview": msg.text[:120]
            }
            for msg, score, reasons in resolved_matches
        ]
    )

    print_resolved_people(resolved_matches)

    if not resolved_matches:
        logger.log(
            step="SAFETY_GUARD",
            message="No reliable identity match found. Avoiding unrelated context leakage.",
            data={
                "action": "Using only incoming message as context"
            }
        )

        console.print(
            Panel(
                "No reliable cross-channel identity match found.\n"
                "Using only the incoming message context to avoid wrong-person leakage.",
                style="yellow"
            )
        )

        resolved_messages = [incoming_message]

    else:
        resolved_messages = [match[0] for match in resolved_matches]

    chunks = build_chunks(resolved_messages)

    logger.log(
        step="CHUNKING",
        message="Built RAG chunks only from resolved person's messages",
        data=[
            {
                "chunk_id": chunk["chunk_id"],
                "source": chunk["source"],
                "person_name": chunk["person_name"],
                "timestamp": chunk["timestamp"],
                "search_text_preview": chunk["search_text"][:150]
            }
            for chunk in chunks
        ]
    )

    rag_query = f"""
    {incoming_message.person_name}
    {incoming_message.subject}
    {incoming_message.text}
    """

    logger.log(
        step="RAG_QUERY",
        message="Created retrieval query from incoming message",
        data={
            "query": rag_query.strip()
        }
    )

    rag_results = retrieve_context(
        query=rag_query,
        chunks=chunks,
        top_k=5
    )

    logger.log(
        step="RAG_RETRIEVAL",
        message="Retrieved most relevant context chunks with similarity scores",
        data=[
            {
                "source": item["source"],
                "timestamp": item["timestamp"],
                "person_name": item["person_name"],
                "rag_score": item["rag_score"],
                "text": item["text"]
            }
            for item in rag_results
        ]
    )

    print_rag_results(rag_results)

    aggregated_context = aggregate_context(
        incoming_message=incoming_message,
        resolved_matches=resolved_matches,
        rag_results=rag_results
    )

    logger.log(
        step="CONTEXT_AGGREGATION",
        message="Aggregated relationship history, sources, RAG context, and open commitments",
        data={
            "person": aggregated_context["person"],
            "sources_found": aggregated_context["sources_found"],
            "open_commitments": aggregated_context["open_commitments"],
            "relationship_history_count": len(aggregated_context["relationship_history"]),
            "rag_context_count": len(aggregated_context["rag_context"])
        }
    )

    tone_profile = get_tone_profile(incoming_message.person_name)

    logger.log(
        step="TONE_PROFILE",
        message="Loaded tone profile for reply generation",
        data=tone_profile
    )

    draft_reply = generate_reply(
        incoming_message=incoming_message,
        aggregated_context=aggregated_context,
        tone_profile=tone_profile
    )

    logger.log(
        step="REPLY_GENERATION",
        message="Generated reply draft using aggregated context and tone profile",
        data={
            "draft_reply": draft_reply
        }
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

        logger.log(
            step="HUMAN_FEEDBACK",
            message="User edited draft reply",
            data={
                "original_draft": draft_reply,
                "edited_reply": edited_reply,
                "saved_as_learning_signal": learned
            }
        )

        console.print("\n[bold green]Final Edited Reply[/bold green]")
        console.print(Panel(edited_reply, style="green"))

        if learned:
            console.print("[cyan]Saved edit as future tone-learning signal.[/cyan]")

    else:
        logger.log(
            step="HUMAN_FEEDBACK",
            message="User approved draft without edits",
            data={
                "approved_reply": draft_reply,
                "saved_as_learning_signal": False
            }
        )

        console.print("[green]Approved draft. MVP does not auto-send.[/green]")

    logger.log(
        step="END",
        message="Operator run completed"
    )

    logger.save()

    console.print(
        Panel(
            "Run logs saved to logs/run_logs.json",
            style="cyan"
        )
    )


if __name__ == "__main__":
    run_operator()