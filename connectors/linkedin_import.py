import csv
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime


def parse_linkedin_csv(csv_path: str) -> List[Dict]:
    """
    Parse LinkedIn messages export CSV
    
    LinkedIn export format typically has columns:
    - FROM
    - TO  
    - DATE
    - CONTENT
    - CONVERSATION ID
    """
    messages = []
    
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for idx, row in enumerate(reader):
                # Skip messages you sent (only import received messages)
                from_name = row.get("FROM", "").strip()
                content = row.get("CONTENT", "").strip()
                date = row.get("DATE", "").strip()
                
                if not content:
                    continue
                
                messages.append({
                    "id": f"linkedin_{idx}",
                    "from_name": from_name,
                    "email": None,  # LinkedIn doesn't expose emails
                    "handle": None,  # Could extract from profile URL if available
                    "company": None,  # Would need manual mapping
                    "timestamp": date,
                    "message": content
                })
        
        print(f"Parsed {len(messages)} LinkedIn messages")
        return messages
    
    except Exception as e:
        print(f"Error parsing LinkedIn CSV: {e}")
        return []


def save_to_json(messages: List[Dict], output_path: str = "data/linkedin_messages.json"):
    """Save parsed messages to JSON"""
    Path(output_path).parent.mkdir(exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2)
    
    print(f"Saved {len(messages)} messages to {output_path}")


def import_linkedin_export(csv_path: str):
    """Main import function"""
    print(f"\nImporting LinkedIn messages from {csv_path}")
    
    messages = parse_linkedin_csv(csv_path)
    
    if messages:
        save_to_json(messages)
        print(f"LinkedIn import complete: {len(messages)} messages")
    else:
        print("No messages found in export")


# CLI usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m connectors.linkedin_import <path_to_linkedin_export.csv>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    import_linkedin_export(csv_path)