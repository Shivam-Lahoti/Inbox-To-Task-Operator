"""
Unified Auto-Processing Server
Monitors Gmail (polling) and SMS (webhook) simultaneously
"""

import os
import time
import threading
from datetime import datetime
from email.utils import parsedate_to_datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Form, BackgroundTasks
from twilio.twiml.messaging_response import MessagingResponse

from connectors.gmail_connector import GmailConnector
from connectors.twilio_connector import TwilioConnector
from core.operator_core import MessageProcessor

load_dotenv()


class UnifiedServer:
    """Unified server for Gmail + SMS auto-processing"""
    
    def __init__(self, my_email: str = "shivam.2199@gmail.com"):
        self.processor = MessageProcessor()
        self.gmail = GmailConnector()
        self.twilio = TwilioConnector()
        self.my_email = my_email
        self.running = True
        
        # Make startup time timezone-aware
        from datetime import timezone
        self.startup_time = datetime.now(timezone.utc)  # Changed this line
        
        self.processed_email_ids = set()
        
        try:
            self.gmail.authenticate()
            print("Gmail authenticated")
            print(f"Server started at {self.startup_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(" Only processing emails received AFTER this time\n")
        except Exception as e:
            print(f" Gmail authentication failed: {e}")
            self.gmail = None
    
    def process_email(self, email_data):
        """Process incoming email"""
        print(f"\nProcessing email from {email_data['from_email']}...")
        
        incoming_data = {
            "id": email_data["id"],
            "from_name": email_data["from_name"],
            "from_email": email_data["from_email"],
            "company": email_data.get("company"),
            "subject": email_data["subject"],
            "body": email_data["body"],
            "timestamp": email_data["timestamp"]
        }
        
        def send_callback(incoming, draft):
            return self.gmail.send_reply(
                thread_id=email_data["thread_id"],
                to_email=incoming.email,
                subject=incoming.subject,
                body=draft
            )
        
        def draft_callback(incoming, draft):
            self.gmail.create_draft_reply(
                thread_id=email_data["thread_id"],
                to_email=incoming.email,
                subject=incoming.subject,
                body=draft
            )
            print(f"Draft created in Gmail")
        
        result = self.processor.process_message(
            source="email",
            raw_message=incoming_data,
            send_callback=send_callback,
            draft_callback=draft_callback
        )
        
        if result.get('action') in ['sent_immediately', 'sent_with_buffer', 'draft_created']:
            self.gmail.mark_as_read(email_data["id"])
        
        return result
    
    def process_sms(self, from_phone, body):
        """Process incoming SMS"""
        print(f"\n Processing SMS from {from_phone}...")
        
        incoming_data = {
            "id": f"sms_{from_phone.replace('+', '')}_{int(time.time())}",
            "from_name": from_phone,
            "phone": from_phone,
            "body": body,
            "timestamp": datetime.now().isoformat()
        }
        
        def send_callback(incoming, draft):
            return self.twilio.send_sms(incoming.phone, draft)
        
        result = self.processor.process_message(
            source="sms",
            raw_message=incoming_data,
            send_callback=send_callback
        )
        
        return result
    
    def gmail_polling_loop(self):
        """Background thread that polls Gmail every 30 seconds"""
        print("Gmail polling started (checking every 30 seconds)")
        print(f" Will ONLY process emails received after {self.startup_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        while self.running:
            try:
                if self.gmail:
                    email = self.gmail.get_latest_unread_email(self.my_email)
                    
                    if email:
                        if email['id'] in self.processed_email_ids:
                            time.sleep(30)
                            continue
                        
                        # DEBUG: Print raw timestamp
                        print(f"DEBUG: Raw timestamp = '{email['timestamp']}'")
                        
                        try:
                            email_time = parsedate_to_datetime(email['timestamp'])
                            print(f" DEBUG: Parsed timestamp = {email_time}")
                            
                            if email_time < self.startup_time:
                                print(f"OLD email (before {self.startup_time.strftime('%H:%M:%S')}), skipping")
                                self.processed_email_ids.add(email['id'])
                                continue
                            else:
                                print(f"\nNEW email from {email['from_email']}")
                                print(f"   Received: {email_time.strftime('%Y-%m-%d %H:%M:%S')}")
                                print(f"   Subject: {email['subject']}")
                                
                                self.process_email(email)
                                self.processed_email_ids.add(email['id'])
                        
                        except Exception as e:
                            # Timestamp parse failed - SKIP to be safe
                            print(f"Cannot parse timestamp for {email['from_email']}: {e}")
                            print(f"   Skipping to avoid processing old emails")
                            self.processed_email_ids.add(email['id'])
                            continue
            
            except Exception as e:
                print(f"Gmail polling error: {e}")
            
        time.sleep(30)
    
    def start_polling(self):
        """Start Gmail polling in background thread"""
        if not self.gmail:
            print("Gmail not available, skipping polling")
            return
        
        polling_thread = threading.Thread(target=self.gmail_polling_loop, daemon=True)
        polling_thread.start()
        print("Gmail polling thread started\n")
    
    def stop(self):
        """Stop the server"""
        self.running = False


server = UnifiedServer()
app = FastAPI()


@app.post("/webhook/sms")
async def receive_sms(
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...)
):
    """Twilio SMS webhook"""
    print(f"\n📱 Incoming SMS from {From}: {Body}")
    background_tasks.add_task(server.process_sms, From, Body)
    
    response = MessagingResponse()
    response.message("Processing your message...")
    return str(response)


@app.get("/")
async def health_check():
    return {
        "status": "Unified Auto-Processor Active",
        "gmail_polling": server.gmail is not None,
        "sms_webhook": True,
        "processed_count": len(server.processor.processed_ids)
    }


@app.get("/status")
async def get_status():
    return {
        "status": "running",
        "gmail_enabled": server.gmail is not None,
        "sms_enabled": True,
        "messages_processed": len(server.processor.processed_ids),
        "emails_processed": len(server.processed_email_ids)
    }


@app.on_event("startup")
async def startup_event():
    server.start_polling()


@app.on_event("shutdown")
async def shutdown_event():
    server.stop()


def start_unified_server(port: int = 8000):
    """Start the unified server"""
    import uvicorn
    
    print("\n" + "="*70)
    print("UNIFIED AUTO-PROCESSOR SERVER")
    print("="*70)
    print("\nGmail: Polling every 30 seconds")
    print(f"SMS: Webhook at http://localhost:{port}/webhook/sms")
    print(f"Status: http://localhost:{port}/status")
    print("\nMake sure ngrok is running:")
    print(f"   ngrok http {port}")
    print("\nSystem will auto-process and reply to both channels")
    print("="*70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")


if __name__ == "__main__":
    port = int(os.getenv("TWILIO_WEBHOOK_PORT", 8000))
    start_unified_server(port)