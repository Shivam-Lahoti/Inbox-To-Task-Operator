"""
Unified message processor - handles both email and SMS
"""

from typing import Dict, Optional
from core.schemas import NormalizedMessage
from core.normalizer import normalize_incoming
from core.source_loader import load_all_sources
from core.normalizer import normalize_all_sources
from core.person_resolution import resolve_person, get_contact_db
from core.chunker import build_chunks
from core.retriever import retrieve_context
from core.context_aggregator import aggregate_context
from core.tone_profile import get_tone_profile
from core.reply_generator import generate_reply
from core.risk_assessor import assess_message_risk, should_auto_send, format_risk_summary
from core.auto_sender import AutoSender, send_immediately
from core.logger import OperatorLogger


class MessageProcessor:
    """Core message processing engine"""
    
    def __init__(self):
        self.logger = OperatorLogger()
        self.auto_sender = AutoSender()
        self.processed_ids = set()
    
    def process_message(
        self,
        source: str,
        raw_message: Dict,
        send_callback: callable,
        draft_callback: Optional[callable] = None
    ) -> Dict:

        
        self.logger.log("START", f"Processing {source} message")
        
        msg_id = raw_message.get("id", "")
        if msg_id in self.processed_ids:
            self.logger.log("SKIP", f"Message {msg_id} already processed")
            return {"status": "skipped", "reason": "already_processed"}
        
        try:
            incoming = normalize_incoming(source, raw_message)
            self.logger.log("NORMALIZED", f"From {incoming.person_name}", {
                "source": source,
                "person": incoming.person_name,
                "preview": incoming.text[:100]
            })
        except Exception as e:
            self.logger.log("ERROR", f"Normalization failed: {e}")
            return {"status": "error", "stage": "normalization", "error": str(e)}
        
        self.logger.log("LOADING_SOURCES", "Loading historical messages")
        raw_sources = load_all_sources()
        all_messages = normalize_all_sources(raw_sources)
        
        # ENRICH incoming message early (extract name, link identifiers)
        db = get_contact_db()
        incoming = db.enrich(incoming)
        
        self.logger.log("RESOLVING_IDENTITY", f"Resolving {incoming.person_name}")
        resolved = resolve_person(incoming, all_messages)
        
        if not resolved:
            resolved = [(incoming, 1.0, ["incoming message"])]
        
        identity_confidence = resolved[0][1] if resolved else 0.0
        sources_found = list(set(msg.source for msg, _, _ in resolved))
        
        self.logger.log("IDENTITY_RESOLVED", f"Confidence: {identity_confidence}", {
            "sources": sources_found,
            "matches": len(resolved)
        })
        
        resolved_messages = [msg for msg, _, _ in resolved]
        chunks = build_chunks(resolved_messages)
        
        query = f"{incoming.subject or ''} {incoming.text}"
        retrieved = retrieve_context(query, chunks, top_k=5)
        
        context = aggregate_context(incoming.person_name, resolved, retrieved)
        
        self.logger.log("CONTEXT_AGGREGATED", "Context ready", {
            "sources": context['sources_found'],
            "total_messages": context['total_messages']
        })
        
        risk_level, risk_reasons = assess_message_risk(
            incoming,
            identity_confidence,
            sources_found
        )
        
        self.logger.log("RISK_ASSESSED", format_risk_summary(risk_level, risk_reasons), {
            "risk_level": risk_level,
            "reasons": risk_reasons
        })
        
        self.logger.log("GENERATING_REPLY", "Calling Claude API")
        tone = get_tone_profile(incoming.person_name)
        
        try:
            draft = generate_reply(incoming.text, context, tone, None)
            self.logger.log("REPLY_GENERATED", f"Draft ready: {draft[:100]}...")
        except Exception as e:
            self.logger.log("ERROR", f"Reply generation failed: {e}")
            return {"status": "error", "stage": "generation", "error": str(e)}
        
        result = {
            "status": "processed",
            "incoming": incoming,
            "context": context,
            "draft": draft,
            "risk_level": risk_level,
            "risk_reasons": risk_reasons,
            "identity_confidence": identity_confidence
        }
        
        should_send, buffer_seconds = should_auto_send(risk_level)
        
        if not should_send:
            self.logger.log("DRAFT_ONLY", "High risk - creating draft for review")
            
            if draft_callback:
                draft_callback(incoming, draft)
                result["action"] = "draft_created"
            else:
                result["action"] = "draft_required"
            
        elif buffer_seconds > 0:
            self.logger.log("BUFFER_SEND", f"Medium risk - {buffer_seconds}s buffer")
            
            def countdown_callback(remaining):
                print(f"Sending in {remaining} seconds... (Press Ctrl+C to cancel)")
            
            def send_function():
                return send_callback(incoming, draft)
            
            success = self.auto_sender.send_with_buffer(
                buffer_seconds,
                send_function,
                on_countdown=countdown_callback
            )
            
            result["action"] = "sent_with_buffer" if success else "cancelled"
            
        else:
            self.logger.log("IMMEDIATE_SEND", "Low risk - sending immediately")
            
            def send_function():
                return send_callback(incoming, draft)
            
            success = send_immediately(send_function)
            result["action"] = "sent_immediately" if success else "send_failed"
        
        self.processed_ids.add(msg_id)
        
        # SAVE MESSAGE TO HISTORY - Real-time RAG learning
        # Save the enriched incoming message (with extracted name)
        if result.get('action') in ['sent_immediately', 'sent_with_buffer', 'draft_created']:
            try:
                from core.message_storage import MessageStorage
                from core.person_resolution import reload_contact_db
                
                storage = MessageStorage()
                saved = storage.save_message(incoming)
                
                if saved:
                    reload_contact_db()
                    print("[STORAGE] Message saved, contact DB reloaded")
            except Exception as e:
                print(f"[STORAGE] Save failed: {e}")
        
        self.logger.log("END", f"Processing complete - {result['action']}")
        self.logger.save()
        
        return result