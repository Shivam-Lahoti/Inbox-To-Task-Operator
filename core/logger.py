import json
from pathlib import Path
from datetime import datetime


LOG_PATH = Path("logs/run_logs.json")


class OperatorLogger:
    def __init__(self):
        self.events = []

    def log(self, step: str, message: str, data=None):
        event = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "step": step,
            "message": message,
            "data": data or {}
        }

        self.events.append(event)

        print(f"\n[LOG] {step}: {message}")

        if data:
            print(json.dumps(data, indent=2, default=str))

    def save(self):
        LOG_PATH.parent.mkdir(exist_ok=True)

        with open(LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.events, f, indent=2, default=str)