import os
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from fastapi import FastAPI, Form, Request
from typing import Dict

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
            print(f"Error sending SMS: {e}")
            return False
    
    def parse_incoming_sms(self, form_data: Dict) -> Dict:
        """Parse incoming Twilio webhook data"""
        return {
            "id": form_data.get("MessageSid", ""),
            "from_name": form_data.get("From", ""),  # Phone number
            "phone": form_data.get("From", ""),
            "email": None,
            "company": None,
            "timestamp": "",  # Twilio doesn't provide timestamp in webhook
            "subject": None,
            "body": form_data.get("Body", ""),
            "source": "sms"
        }


# FastAPI webhook server
app = FastAPI()
twilio_connector = TwilioConnector()


# Store for webhook data (in production, use a queue/database)
latest_sms = None


@app.post("/webhook/sms")
async def receive_sms(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...)
):
    """Twilio webhook endpoint"""
    global latest_sms
    
    print(f"\nIncoming SMS from {From}")
    print(f"Message: {Body}")
    
    # Parse incoming SMS
    latest_sms = {
        "From": From,
        "Body": Body,
        "MessageSid": MessageSid
    }
    
    # Return TwiML response (acknowledge receipt)
    response = MessagingResponse()
    response.message("Message received. Processing...")
    
    return str(response)


@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "Twilio webhook server running"}


@app.get("/latest-sms")
async def get_latest_sms():
    """Get latest received SMS (for testing)"""
    if latest_sms:
        return latest_sms
    return {"message": "No SMS received yet"}


def start_webhook_server(port: int = 8000):
    """Start FastAPI webhook server"""
    import uvicorn
    print(f"\n🚀 Starting Twilio webhook server on port {port}")
    print(f"Webhook URL: http://localhost:{port}/webhook/sms")
    print("\nRemember to expose this with ngrok for Twilio to reach it:")
    print(f"   ngrok http {port}")
    
    uvicorn.run(app, host="0.0.0.0", port=port)


# CLI usage
if __name__ == "__main__":
    port = int(os.getenv("TWILIO_WEBHOOK_PORT", 8000))
    start_webhook_server(port)