import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from core.logger import OperatorLogger
from core.source_loader import load_all_sources, load_test_cases
from core.normalizer import normalize_all_sources, normalize_incoming
from core.person_resolution import resolve_person
from core.chunker import build_chunks
from core.retriever import retrieve_context
from core.context_aggregator import aggregate_context
from core.tone_profile import get_tone_profile
from core.reply_generator import generate_reply
from core.feedback_learning import learn_from_user_edit

from connectors.gmail_connector import GmailConnector
from connectors.twilio_connector import TwilioConnector


console = Console()


def print_header():
    """Print application header"""
    console.print(Panel.fit(
        "[bold cyan]Cross-Channel Relationship-Aware Reply Operator[/bold cyan]\n"
        "[dim]Intelligent replies using multi-platform context[/dim]",
        border_style="cyan"
    ))


def demo_mode():
    """Run in demo mode with test cases"""
    logger = OperatorLogger()
    
    logger.log("START", "Starting operator in DEMO mode")
    
    # Load sources
    logger.log("SOURCE_LOADING", "Loading historical messages from all platforms")
    raw_sources = load_all_sources()
    
    # Normalize
    logger.log("NORMALIZATION", "Normalizing messages to common schema")
    all_messages = normalize_all_sources(raw_sources)
    
    # Load test cases
    test_cases = load_test_cases()
    
    if not test_cases:
        console.print(" No test cases found in data/test_cases.json")
        return
    
    # Select test case
    console.print("\n[bold]Available Test Cases:[/bold]")
    for idx, case in enumerate(test_cases, 1):
        console.print(f"{idx}. {case.get('description', 'Test case')}")
    
    choice = Prompt.ask("\nSelect test case", choices=[str(i) for i in range(1, len(test_cases) + 1)])
    selected_case = test_cases[int(choice) - 1]
    
    # Normalize incoming
    logger.log("INCOMING_MESSAGE", f"Processing incoming {selected_case['source']} message")
    incoming = normalize_incoming(selected_case["source"], selected_case)
    
    console.print(f"\n[bold]Incoming Message:[/bold]")
    console.print(f"From: {incoming.person_name}")
    console.print(f"Source: {incoming.source}")
    console.print(f"Subject: {incoming.subject}")
    console.print(f"Body: {incoming.text[:200]}...")
    
    # Resolve person
    logger.log("PERSON_RESOLUTION", f"Resolving identity for {incoming.person_name}")
    resolved = resolve_person(incoming, all_messages)
    
    if not resolved:
        logger.log("SAFETY_GUARD", "No strong identity match found", {
            "person": incoming.person_name,
            "action": "Using only incoming message context"
        })
        resolved = [(incoming, 1.0, ["incoming message"])]
    
    console.print(f"\n[bold]Identity Resolution:[/bold]")
    console.print(f"Found {len(resolved)} matching messages across platforms")
    
    sources_found = set()
    for msg, score, reasons in resolved[:5]:
        sources_found.add(msg.source)
        console.print(f"  • [{msg.source}] {msg.person_name} (confidence: {score}) - {', '.join(reasons)}")
    
    # Build chunks
    logger.log("CHUNKING", "Building searchable chunks from resolved messages")
    resolved_messages = [msg for msg, _, _ in resolved]
    chunks = build_chunks(resolved_messages)
    
    # Retrieve context
    query = f"{incoming.subject or ''} {incoming.text}"
    logger.log("RAG_QUERY", f"RAG query: {query[:100]}...")
    
    retrieved = retrieve_context(query, chunks, top_k=5)
    logger.log("RAG_RETRIEVAL", f"Retrieved {len(retrieved)} relevant chunks")
    
    # Aggregate context
    logger.log("CONTEXT_AGGREGATION", "Aggregating cross-platform context")
    context = aggregate_context(incoming.person_name, resolved, retrieved)
    
    console.print(f"\n[bold]Aggregated Context:[/bold]")
    console.print(f"Sources: {', '.join(context['sources_found'])}")
    console.print(f"Total messages: {context['total_messages']}")
    console.print(f"Open commitments: {len(context['open_commitments'])}")
    
    # Load tone profile
    logger.log("TONE_PROFILE", f"Loading tone profile for {incoming.person_name}")
    tone = get_tone_profile(incoming.person_name)
    
    # Generate reply
    logger.log("REPLY_GENERATION", "Generating reply using Claude")
    console.print("\n [dim]Generating reply...[/dim]")
    
    draft = generate_reply(incoming.text, context, tone, None)
    
    console.print(f"\n[bold green]Generated Draft Reply:[/bold green]")
    console.print(Panel(draft, border_style="green"))
    
    # Human feedback
    logger.log("HUMAN_FEEDBACK", "Awaiting human review")
    
    if Confirm.ask("\nWould you like to edit this draft?"):
        console.print("\n[dim]Paste your edited version (press Enter twice when done):[/dim]")
        edited_lines = []
        while True:
            line = input()
            if not line:
                break
            edited_lines.append(line)
        
        edited = "\n".join(edited_lines)
        
        if edited.strip():
            learn_from_user_edit(incoming.person_name, draft, edited)
            draft = edited
    
    logger.log("END", "Demo completed successfully", {
        "person": incoming.person_name,
        "sources_used": context['sources_found'],
        "reply_length": len(draft)
    })
    
    logger.save()
    
    console.print("\n [bold green]Demo completed![/bold green]")


def gmail_mode():
    """Run in Gmail live mode"""
    logger = OperatorLogger()
    
    logger.log("START", "Starting operator in GMAIL mode")
    
    # Initialize Gmail
    console.print("\n[bold]Gmail Mode[/bold]")
    gmail = GmailConnector()
    
    try:
        gmail.authenticate()
    except Exception as e:
        console.print(f" Gmail authentication failed: {e}")
        return
    
    # Get latest unread email
    console.print("\n🔍 Fetching latest unread email...")
    email = gmail.get_latest_unread_email()
    
    if not email:
        console.print("📭 No unread emails found")
        return
    
    # Load sources
    logger.log("SOURCE_LOADING", "Loading historical messages")
    raw_sources = load_all_sources()
    all_messages = normalize_all_sources(raw_sources)
    
    # Normalize incoming email
    incoming_data = {
        "id": email["id"],
        "from_name": email["from_name"],
        "from_email": email["from_email"],
        "company": email.get("company"),
        "subject": email["subject"],
        "body": email["body"],
        "timestamp": email["timestamp"]
    }
    
    incoming = normalize_incoming("email", incoming_data)
    
    console.print(f"\n[bold]Incoming Email:[/bold]")
    console.print(f"From: {incoming.person_name} <{incoming.email}>")
    console.print(f"Subject: {incoming.subject}")
    console.print(f"Body: {incoming.text[:300]}...")
    
    # Resolve person across platforms
    logger.log("PERSON_RESOLUTION", f"Resolving {incoming.person_name} across all platforms")
    resolved = resolve_person(incoming, all_messages)
    
    if not resolved:
        resolved = [(incoming, 1.0, ["incoming message"])]
    
    console.print(f"\n [bold]Cross-Platform Identity:[/bold]")
    sources_found = set()
    for msg, score, reasons in resolved[:5]:
        sources_found.add(msg.source)
        console.print(f"  • [{msg.source}] {', '.join(reasons)} (confidence: {score})")
    
    # Build chunks and retrieve
    resolved_messages = [msg for msg, _, _ in resolved]
    chunks = build_chunks(resolved_messages)
    
    query = f"{incoming.subject or ''} {incoming.text}"
    retrieved = retrieve_context(query, chunks, top_k=5)
    
    # Aggregate context
    context = aggregate_context(incoming.person_name, resolved, retrieved)
    
    console.print(f"\n [bold]Context Summary:[/bold]")
    console.print(f"Sources found: {', '.join(context['sources_found'])}")
    console.print(f"Total messages: {context['total_messages']}")
    
    # Generate reply
    tone = get_tone_profile(incoming.person_name)
    
    console.print("\n[dim]Generating reply with Claude...[/dim]")
    draft = generate_reply(incoming.text, context, tone, None)
    
    console.print(f"\n [bold green]Generated Draft:[/bold green]")
    console.print(Panel(draft, border_style="green"))
    
    # Ask: Draft or Send?
    console.print("\n[bold]What would you like to do?[/bold]")
    console.print("1. Create Gmail draft (review before sending)")
    console.print("2. Send email immediately")
    console.print("3. Cancel")
    
    action = Prompt.ask("Choose", choices=["1", "2", "3"])
    
    if action == "1":
        # Create draft
        success = gmail.create_draft_reply(
            thread_id=email["thread_id"],
            to_email=incoming.email,
            subject=incoming.subject,
            body=draft
        )
        
        if success:
            console.print("\n[bold green]Gmail draft created![/bold green]")
            console.print("Check your Gmail drafts to review and send.")
            gmail.mark_as_read(email["id"])
        else:
            console.print("\nFailed to create draft")
    
    elif action == "2":
        # Send immediately
        if Confirm.ask("\nSend this email immediately without further review?"):
            success = gmail.send_reply(
                thread_id=email["thread_id"],
                to_email=incoming.email,
                subject=incoming.subject,
                body=draft
            )
            
            if success:
                console.print("\n[bold green]Email sent![/bold green]")
                gmail.mark_as_read(email["id"])
            else:
                console.print("\n[bold red]Failed to send email[/bold red]")
    else:
        console.print("\nCancelled")
    
    logger.log("END", "Gmail mode completed")
    logger.save()


def sms_mode():
    """Run in SMS live mode"""
    logger = OperatorLogger()
    
    logger.log("START", "Starting operator in SMS mode")
    
    # Initialize Twilio
    console.print("\n📱 [bold]SMS Mode[/bold]")
    
    try:
        from connectors.twilio_connector import TwilioConnector
        twilio = TwilioConnector()
    except ValueError as e:
        console.print(f"❌ Twilio configuration error: {e}")
        console.print("\nMake sure your .env has:")
        console.print("TWILIO_ACCOUNT_SID=...")
        console.print("TWILIO_AUTH_TOKEN=...")
        console.print("TWILIO_PHONE_NUMBER=...")
        return
    
    console.print("\n⚠️  Make sure webhook server is running:")
    console.print("   python -m connectors.twilio_connector")
    console.print("\nWaiting for incoming SMS...")
    console.print("Send a test message to your Twilio number to trigger the operator.\n")
    
    # For now, we'll use a manual trigger
    # In production, this would be event-driven from the webhook
    
    console.print("📱 [bold]Manual SMS Test[/bold]")
    
    from_phone = Prompt.ask("Enter sender's phone number (e.g., +14155551234)")
    from_name = Prompt.ask("Enter sender's name (e.g., John Doe)")
    message_body = Prompt.ask("Enter the SMS message")
    
    # Load sources
    logger.log("SOURCE_LOADING", "Loading historical messages")
    raw_sources = load_all_sources()
    all_messages = normalize_all_sources(raw_sources)
    
    # Normalize incoming SMS
    incoming_data = {
        "id": "sms_live_001",
        "from_name": from_name,
        "phone": from_phone,
        "email": None,
        "company": None,
        "timestamp": "",
        "subject": None,
        "body": message_body
    }
    
    incoming = normalize_incoming("sms", incoming_data)
    
    console.print(f"\n📱 [bold]Incoming SMS:[/bold]")
    console.print(f"From: {incoming.person_name} ({incoming.phone})")
    console.print(f"Message: {incoming.text}")
    
    # Resolve person across platforms
    logger.log("PERSON_RESOLUTION", f"Resolving {incoming.person_name} across all platforms")
    resolved = resolve_person(incoming, all_messages)
    
    if not resolved:
        resolved = [(incoming, 1.0, ["incoming message"])]
    
    console.print(f"\n🔍 [bold]Cross-Platform Identity:[/bold]")
    sources_found = set()
    for msg, score, reasons in resolved[:5]:
        sources_found.add(msg.source)
        console.print(f"  • [{msg.source}] {', '.join(reasons)} (confidence: {score})")
    
    # Build chunks and retrieve
    resolved_messages = [msg for msg, _, _ in resolved]
    chunks = build_chunks(resolved_messages)
    
    query = message_body
    retrieved = retrieve_context(query, chunks, top_k=5)
    
    # Aggregate context
    context = aggregate_context(incoming.person_name, resolved, retrieved)
    
    console.print(f"\n📊 [bold]Context Summary:[/bold]")
    console.print(f"Sources found: {', '.join(context['sources_found'])}")
    console.print(f"Total messages: {context['total_messages']}")
    
    # Show cross-platform context
    if len(sources_found) > 1:
        console.print(f"\n✨ [bold green]Cross-platform intelligence activated![/bold green]")
        console.print(f"Found context from: {', '.join(sources_found)}")
    
    # Generate reply
    tone = get_tone_profile(incoming.person_name)
    
    console.print("\n⏳ [dim]Generating reply with Claude...[/dim]")
    draft = generate_reply(message_body, context, tone, None)
    
    console.print(f"\n📱 [bold green]Generated SMS Reply:[/bold green]")
    console.print(Panel(draft, border_style="green"))
    
    # Ask: Send or Cancel?
    if Confirm.ask("\nSend this SMS reply?"):
        success = twilio.send_sms(from_phone, draft)
        
        if success:
            console.print("\n✅ [bold green]SMS sent![/bold green]")
        else:
            console.print("\n❌ Failed to send SMS")
    else:
        console.print("\n❌ Cancelled")
    
    logger.log("END", "SMS mode completed")
    logger.save()

def main():
    """Main entry point"""
    print_header()
    
    console.print("\n[bold]Select Mode:[/bold]")
    console.print("1. Demo Mode (test cases with mock data)")
    console.print("2. Gmail Mode (live email trigger)")
    console.print("3. SMS Mode (Twilio webhook)")
    console.print("4. Exit")
    
    choice = Prompt.ask("\nChoose", choices=["1", "2", "3", "4"])
    
    if choice == "1":
        demo_mode()
    elif choice == "2":
        gmail_mode()
    elif choice == "3":
        sms_mode()
    else:
        console.print("\nGoodbye!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n Interrupted by user")
        sys.exit(0)