from typing import List, Dict
from core.schemas import NormalizedMessage


def extract_open_commitments(chunks: List[Dict]) -> List[str]:
    """Extract open commitments from conversation history"""
    commitment_keywords = [
        "available", "call", "tomorrow", "confirming", 
        "discuss", "intro", "meeting", "schedule", "free"
    ]
    
    commitments = []
    
    for chunk in chunks:
        text_lower = chunk["text"].lower()
        
        if any(keyword in text_lower for keyword in commitment_keywords):
            commitments.append(
                f"[{chunk['source']}] {chunk['timestamp']}: {chunk['text'][:150]}"
            )
    
    return commitments[:5]  # Top 5 commitments


def aggregate_context(
    person_name: str,
    resolved_messages: List[tuple],
    retrieved_chunks: List[Dict]
) -> Dict:
    """
    Aggregate all context about a person from multiple sources
    
    Args:
        person_name: Name of the person
        resolved_messages: List of (message, score, reasons) tuples
        retrieved_chunks: RAG-retrieved relevant chunks
    
    Returns:
        Aggregated context dictionary
    """
    
    # Group messages by source
    sources_found = set()
    relationship_history = []
    
    for msg, score, reasons in resolved_messages:
        sources_found.add(msg.source)
        
        relationship_history.append({
            "source": msg.source,
            "timestamp": msg.timestamp,
            "confidence": score,
            "reasons": reasons,
            "subject": msg.subject,
            "preview": msg.text[:200] if msg.text else ""
        })
    
    # Build RAG context
    rag_context = []
    for chunk in retrieved_chunks:
        rag_context.append({
            "source": chunk["source"],
            "timestamp": chunk["timestamp"],
            "relevance": chunk.get("relevance_score", 0),
            "text": chunk["text"]
        })
    
    # Extract commitments
    open_commitments = extract_open_commitments(retrieved_chunks)
    
    return {
        "person": person_name,
        "sources_found": list(sources_found),
        "total_messages": len(resolved_messages),
        "relationship_history": relationship_history[:10],  # Top 10
        "rag_context": rag_context,
        "open_commitments": open_commitments
    }