import os
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from fastapi import FastAPI, Form, Request, BackgroundTasks
from typing import Dict
import asyncio

load_dotenv()


class TwilioConnector:
    """Twilio SMS connector for receiving and sending messages"""
    
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        if not all([self.account_sid, self.auth_token, self.phone_number]):
            raise ValueError("Missing Twilio credentials in .env file")
        
        self.client = Client(self.account_sid, self.auth_token)
    
    def send_sms(self, to_phone: str, message: str) -> bool:
        """Send SMS reply"""
        try:
            response = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=to_phone
            )
            
            print(f"SMS sent to {to_phone}: {response.sid}")
            return True
        
        except Exception as e:
            print(f" Error sending SMS: {e}")
            return False
    
    def parse_incoming_sms(self, form_data: Dict) -> Dict:
        """Parse incoming Twilio webhook data"""
        return {
            "id": form_data.get("MessageSid", ""),
            "from_name": form_data.get("From", ""),
            "phone": form_data.get("From", ""),
            "email": None,
            "company": None,
            "timestamp": "",
            "subject": None,
            "body": form_data.get("Body", "")
        }


# FastAPI webhook server
app = FastAPI()

# Import processor here (after app is created)
from core.operator_core import MessageProcessor

twilio_connector = TwilioConnector()
processor = MessageProcessor()


def process_sms_background(from_phone: str, from_name: str, body: str):
    """Process SMS in background"""
    print(f"\nProcessing SMS from {from_phone}...")
    
    # Prepare message data
    incoming_data = {
        "id": f"sms_webhook_{from_phone.replace('+', '')}",
        "from_name": from_name,
        "phone": from_phone,
        "body": body,
        "timestamp": ""
    }
    
    # Define send callback
    def send_callback(incoming, draft):
        """Send SMS reply"""
        return twilio_connector.send_sms(incoming.phone, draft)
    
    # Process message
    result = processor.process_message(
        source="sms",
        raw_message=incoming_data,
        send_callback=send_callback
    )
    
    print(f"\nSMS Processing Complete!")
    print(f"Risk Level: {result.get('risk_level')}")
    print(f"Action: {result.get('action')}")
    print(f"Reply: {result.get('draft', '')[:100]}...")


@app.post("/webhook/sms")
async def receive_sms(
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...)
):
    """
    Twilio webhook endpoint - receives SMS and auto-processes
    """
    
    print(f"\nIncoming SMS from {From}")
    print(f"Message: {Body}")
    
    # Extract sender name from phone (or use phone as name)
    from_name = From  # Can be enhanced with contact lookup
    
    # Process in background so we can return quickly to Twilio
    background_tasks.add_task(process_sms_background, From, from_name, Body)
    
    # Return TwiML response immediately (acknowledge receipt)
    response = MessagingResponse()
    response.message("Processing your message...")
    
    return str(response)


@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "SMS Auto-Processor Active",
        "message": "Send SMS to Twilio number to trigger auto-processing"
    }


@app.get("/status")
async def get_status():
    """Get processor status"""
    return {
        "status": "active",
        "processed_count": len(processor.processed_ids)
    }


def start_webhook_server(port: int = 8000):
    """Start FastAPI webhook server"""
    import uvicorn
    
    print("\n" + "="*60)
    print("SMS AUTO-PROCESSOR WEBHOOK SERVER")
    print("="*60)
    print(f"\nWebhook URL: http://localhost:{port}/webhook/sms")
    print(f"Status: http://localhost:{port}/status")
    print("\n Make sure ngrok is running:")
    print(f"   ngrok http {port}")
    print("\nWhen SMS arrives → Auto-processes → Auto-sends reply")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


# CLI usage
if __name__ == "__main__":
    port = int(os.getenv("TWILIO_WEBHOOK_PORT", 8000))
    start_webhook_server(port)