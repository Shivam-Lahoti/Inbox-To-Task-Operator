import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from core.schemas import NormalizedMessage


DATA_DIR = Path("data")


class MessageStorage:
    """Handles saving and loading messages from JSON files"""
    
    def __init__(self):
        self.email_file = DATA_DIR / "email_messages.json"
        self.linkedin_file = DATA_DIR / "linkedin_messages.json"
        self.whatsapp_file = DATA_DIR / "whatsapp_messages.json"
        self.sms_file = DATA_DIR / "sms_messages.json"
        
        DATA_DIR.mkdir(exist_ok=True)
        
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """Create empty JSON files if they don't exist"""
        for file_path in [self.email_file, self.linkedin_file, self.whatsapp_file, self.sms_file]:
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump([], f)
    
    def _load_json(self, file_path: Path) -> List[Dict]:
        """Load JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def _save_json(self, file_path: Path, data: List[Dict]):
        """Save JSON file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def save_message(self, message: NormalizedMessage):
        """Save a processed message to appropriate source file"""
        
        file_map = {
            "email": self.email_file,
            "linkedin": self.linkedin_file,
            "whatsapp": self.whatsapp_file,
            "sms": self.sms_file
        }
        
        file_path = file_map.get(message.source)
        if not file_path:
            print(f"Unknown source: {message.source}")
            return False
        
        messages = self._load_json(file_path)
        
        if any(msg.get('id') == message.id for msg in messages):
            return False
        
        new_message = self._message_to_dict(message)
        
        messages.append(new_message)
        self._save_json(file_path, messages)
        
        print(f"Saved {message.source} message from {message.person_name} to history")
        
        # Update cross-references in other files
        self.update_cross_references(message)
        
        return True
    
    def _message_to_dict(self, message: NormalizedMessage) -> Dict:
        """Convert NormalizedMessage to JSON-serializable dict"""
        
        if message.source == "email":
            return {
                "id": message.id,
                "from_name": message.person_name,
                "from_email": message.email,
                "company": message.company,
                "timestamp": message.timestamp or datetime.now().isoformat(),
                "subject": message.subject,
                "body": message.text
            }
        
        elif message.source == "sms":
            return {
                "id": message.id,
                "from_name": message.person_name,
                "phone": message.phone,
                "timestamp": message.timestamp or datetime.now().isoformat(),
                "message": message.text
            }
        
        elif message.source == "linkedin":
            return {
                "id": message.id,
                "from_name": message.person_name,
                "email": message.email,
                "handle": message.handle,
                "company": message.company,
                "timestamp": message.timestamp or datetime.now().isoformat(),
                "message": message.text
            }
        
        elif message.source == "whatsapp":
            return {
                "id": message.id,
                "from_name": message.person_name,
                "phone": message.phone,
                "timestamp": message.timestamp or datetime.now().isoformat(),
                "message": message.text
            }
        
        return {}
    def update_cross_references(self, message: NormalizedMessage):
        """Update existing messages with cross-channel identifiers"""
        
        # If this message has both email and phone, update other messages with same person
        if message.email and message.phone:
            # Update SMS/WhatsApp messages with this person's email
            for source in ["sms", "whatsapp"]:
                file_map = {
                    "sms": self.sms_file,
                    "whatsapp": self.whatsapp_file
                }
                
                file_path = file_map.get(source)
                if not file_path:
                    continue
                
                messages = self._load_json(file_path)
                updated = False
                
                for msg in messages:
                    # Find messages with same phone but no email
                    if msg.get("phone") == message.phone and not msg.get("email"):
                        msg["email"] = message.email
                        msg["from_name"] = message.person_name  # Update to full name
                        updated = True
                        print(f"[CROSS_REF] Updated {source} message with email: {message.email}")
                
                if updated:
                    self._save_json(file_path, messages)
        
        # If this message has both email and phone, update email messages with phone
        if message.email and message.phone:
            messages = self._load_json(self.email_file)
            updated = False
            
            for msg in messages:
                # Find messages with same email but no phone
                if msg.get("from_email") == message.email and not msg.get("phone"):
                    msg["phone"] = message.phone
                    updated = True
                    print(f"[CROSS_REF] Updated email message with phone: {message.phone}")
            
            if updated:
                self._save_json(self.email_file, messages)