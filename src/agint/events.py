import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def utc_now() -> str:
  return datetime.now(timezone.utc).isoformat()

def append_event(event_log_path: Path, event_type: str, payload: dict[str, Any]) -> None:
  event_log_path.parent.mkdir(parents=True, exist_ok=True) 

  event = {
    "type": event_type,
    "created_at": utc_now(),
    **payload,
  }
  
  with event_log_path.open("a", encoding="utf-8") as f:
    f.write(json.dumps(event, ensure_ascii=False) + "\n")
  