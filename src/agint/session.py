from datetime import datetime, timezone
from uuid import uuid4


def create_session_id(prefix: str = "cli") -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    short_id = uuid4().hex[:8]
    return f"{prefix}-{timestamp}-{short_id}"
