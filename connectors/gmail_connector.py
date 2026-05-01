import os
import pickle
from pathlib import Path
from typing import Optional, Dict, List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64


# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]


class GmailConnector:
    """Gmail API connector for reading emails and creating drafts"""
    
    def __init__(self):
        self.credentials_file = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials/gmail_credentials.json")
        self.token_file = os.getenv("GMAIL_TOKEN_FILE", "credentials/gmail_token.json")
        self.service = None
    
    def authenticate(self):
        """Authenticate with Gmail API"""
        creds = None
        
        # Check if token file exists
        if Path(self.token_file).exists():
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing Gmail credentials...")
                creds.refresh(Request())
            else:
                print("Starting Gmail OAuth flow...")
                if not Path(self.credentials_file).exists():
                    raise FileNotFoundError(
                        f"Gmail credentials file not found: {self.credentials_file}\n"
                        "Please download OAuth credentials from Google Cloud Console"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials
            Path(self.token_file).parent.mkdir(exist_ok=True)
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
            
            print("Gmail authentication successful")
        
        self.service = build('gmail', 'v1', credentials=creds)
        return self.service
    
    def get_latest_unread_email(self) -> Optional[Dict]:
        """Get the latest unread email"""
        if not self.service:
            self.authenticate()
        
        try:
            # Search for unread messages
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=1
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                print("📭 No unread emails found")
                return None
            
            # Get full message details
            msg_id = messages[0]['id']
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            
            return self._parse_message(message)
        
        except Exception as e:
            print(f"Error fetching email: {e}")
            return None
    
    def _parse_message(self, message: Dict) -> Dict:
        """Parse Gmail message into our format"""
        headers = message['payload']['headers']
        
        # Extract headers
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
        
        # Parse from header: "Name <email@example.com>"
        from_name = from_header.split('<')[0].strip().strip('"')
        from_email = from_header.split('<')[-1].strip('>').strip() if '<' in from_header else from_header
        
        # Extract body
        body = self._get_message_body(message['payload'])
        
        # Extract thread ID
        thread_id = message.get('threadId', '')
        
        return {
            "id": message['id'],
            "thread_id": thread_id,
            "from_name": from_name,
            "from_email": from_email,
            "company": None,  # Would need to extract from signature or lookup
            "subject": subject,
            "body": body,
            "timestamp": date,
            "raw_message": message
        }
    
    def _get_message_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        if 'body' in payload and 'data' in payload['body']:
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        
        # Handle multipart messages
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        
        return ""
    
    def create_draft_reply(self, thread_id: str, to_email: str, subject: str, body: str) -> bool:
        """Create a Gmail draft reply"""
        if not self.service:
            self.authenticate()
        
        try:
            # Create message
            message = MIMEText(body)
            message['to'] = to_email
            message['subject'] = f"Re: {subject}" if not subject.startswith('Re:') else subject
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Create draft
            draft = {
                'message': {
                    'raw': raw_message,
                    'threadId': thread_id
                }
            }
            
            draft_response = self.service.users().drafts().create(
                userId='me',
                body=draft
            ).execute()
            
            print(f"Gmail draft created: {draft_response['id']}")
            return True
        
        except Exception as e:
            print(f"Error creating draft: {e}")
            return False
    
    def send_reply(self, thread_id: str, to_email: str, subject: str, body: str) -> bool:
        """Send a Gmail reply immediately"""
        if not self.service:
            self.authenticate()
        
        try:
            # Create message
            message = MIMEText(body)
            message['to'] = to_email
            message['subject'] = f"Re: {subject}" if not subject.startswith('Re:') else subject
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send message
            send_message = {
                'raw': raw_message,
                'threadId': thread_id
            }
            
            sent_response = self.service.users().messages().send(
                userId='me',
                body=send_message
            ).execute()
            
            print(f"Email sent: {sent_response['id']}")
            return True
        
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def mark_as_read(self, message_id: str):
        """Mark message as read"""
        if not self.service:
            self.authenticate()
        
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            print(f"Marked message {message_id} as read")
        except Exception as e:
            print(f"Could not mark as read: {e}")


# CLI test
if __name__ == "__main__":
    connector = GmailConnector()
    connector.authenticate()
    
    email = connector.get_latest_unread_email()
    if email:
        print("\nLatest unread email:")
        print(f"From: {email['from_name']} <{email['from_email']}>")
        print(f"Subject: {email['subject']}")
        print(f"Body preview: {email['body'][:200]}...")