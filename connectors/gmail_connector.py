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
import re


# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]


def is_real_personal_email(from_email: str, from_name: str, subject: str, body: str) -> bool:
    """
    STRICT whitelist: Only return True for genuine person-to-person emails.
    Default to False (skip) unless ALL checks pass.
    """
    
    from_lower = from_email.lower()
    from_name_lower = from_name.lower()
    subject_lower = subject.lower()
    body_lower = body[:2000].lower()
    
    # Extract domain
    domain = from_email.split('@')[-1].lower() if '@' in from_email else ""
    
    # RULE 1: Must be from personal email domain (WHITELIST)
    personal_domains = [
        "gmail.com", "googlemail.com",
        "yahoo.com", "yahoo.co.in",
        "outlook.com", "hotmail.com", "live.com",
        "icloud.com", "me.com", "mac.com",
        "protonmail.com", "proton.me",
        "aol.com"
    ]
    
    if not any(domain.endswith(personal) for personal in personal_domains):
        return False  # Not from personal domain
    
    # RULE 2: Must NOT be no-reply
    noreply_patterns = ["noreply", "no-reply", "donotreply", "do-not-reply", "mailer-daemon"]
    if any(pattern in from_lower for pattern in noreply_patterns):
        return False
    
    # RULE 3: Must NOT have automated sender patterns
    automated_patterns = [
        "notification", "alert", "digest", "updates",
        "automated", "bot@", "system@"
    ]
    if any(pattern in from_lower for pattern in automated_patterns):
        return False
    
    # RULE 4: Sender name must look like a real person
    fake_name_patterns = [
        "team", "support", "help", "service", "info",
        "sales", "marketing", "no-reply", "noreply",
        "notification", "automated", "system"
    ]
    if any(pattern in from_name_lower for pattern in fake_name_patterns):
        return False
    
    # RULE 5: Must NOT have unsubscribe link
    if "unsubscribe" in body_lower:
        return False
    
    # RULE 6: Body must NOT be mostly HTML template
    html_density = body_lower.count('<') + body_lower.count('>')
    if html_density > 50:
        return False
    
    # RULE 7: Must NOT have bulk email keywords
    bulk_body_keywords = [
        "click here", "shop now", "limited time", "offer expires",
        "discount code", "% off", "free shipping", "buy now",
        "don't miss", "last chance", "hurry", "act now",
        "this email was sent to", "you're receiving this"
    ]
    if any(keyword in body_lower for keyword in bulk_body_keywords):
        return False
    
    # RULE 8: Subject must NOT have marketing language
    marketing_subjects = [
        "discount", "% off", "offer", "sale", "deal",
        "limited time", "expires", "free shipping",
        "shop now", "buy now", "don't miss"
    ]
    if any(keyword in subject_lower for keyword in marketing_subjects):
        return False
    
    # RULE 9: Must have actual readable text content
    text_only = re.sub(r'<[^>]+>', '', body)
    readable_chars = len([c for c in text_only if c.isalpha() or c.isspace()])
    
    if readable_chars < 20:
        return False
    
    # Passed all checks - this is a real personal email
    return True


class GmailConnector:
    """Gmail API connector for reading emails and creating drafts"""
    
    def __init__(self):
        self.credentials_file = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials/gmail_credentials.json")
        self.token_file = os.getenv("GMAIL_TOKEN_FILE", "credentials/gmail_token.json")
        self.service = None
    
    def authenticate(self):
        """Authenticate with Gmail API"""
        creds = None
        
        if Path(self.token_file).exists():
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
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
            
            Path(self.token_file).parent.mkdir(exist_ok=True)
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
            
            print("Gmail authentication successful")
        
        self.service = build('gmail', 'v1', credentials=creds)
        return self.service
    
    def get_latest_unread_email(self, my_email: str = "shivam.2199@gmail.com") -> Optional[Dict]:
        """Get the latest unread PERSONAL email (strict filtering)"""
        if not self.service:
            self.authenticate()
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=f'is:unread -from:{my_email}',
                maxResults=20
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return None
            
            for msg_info in messages:
                msg_id = msg_info['id']
                message = self.service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format='full'
                ).execute()
                
                parsed = self._parse_message(message)
                
                if is_real_personal_email(
                    parsed['from_email'],
                    parsed['from_name'],
                    parsed['subject'],
                    parsed['body']
                ):
                    return parsed
                else:
                    # Skip promotional, but don't mark as read
                    continue
            
            return None
        
        except Exception as e:
            print(f"Error fetching email: {e}")
            return None
    
    def _parse_message(self, message: Dict) -> Dict:
        """Parse Gmail message into our format"""
        headers = message['payload']['headers']
        
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
        
        from_name = from_header.split('<')[0].strip().strip('"')
        from_email = from_header.split('<')[-1].strip('>').strip() if '<' in from_header else from_header
        
        if not from_name or from_name == from_email:
            from_name = from_email.split('@')[0]
        
        body = self._get_message_body(message['payload'])
        thread_id = message.get('threadId', '')
        
        return {
            "id": message['id'],
            "thread_id": thread_id,
            "from_name": from_name,
            "from_email": from_email,
            "company": None,
            "subject": subject,
            "body": body,
            "timestamp": date,
            "raw_message": message
        }
    
    def _get_message_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        if 'body' in payload and 'data' in payload['body']:
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                elif part['mimeType'] == 'text/html' and 'parts' not in payload:
                    if 'data' in part['body']:
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
        
        return ""
    
    def create_draft_reply(self, thread_id: str, to_email: str, subject: str, body: str) -> bool:
        """Create a Gmail draft reply"""
        if not self.service:
            self.authenticate()
        
        try:
            message = MIMEText(body)
            message['to'] = to_email
            message['subject'] = f"Re: {subject}" if not subject.startswith('Re:') else subject
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
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
            message = MIMEText(body)
            message['to'] = to_email
            message['subject'] = f"Re: {subject}" if not subject.startswith('Re:') else subject
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
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
        except:
            pass


if __name__ == "__main__":
    connector = GmailConnector()
    connector.authenticate()
    
    email = connector.get_latest_unread_email()
    if email:
        print("\nLatest unread email:")
        print(f"From: {email['from_name']} <{email['from_email']}>")
        print(f"Subject: {email['subject']}")
        print(f"Body preview: {email['body'][:200]}...")