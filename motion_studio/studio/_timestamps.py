"""UTC timestamp formatting shared by persistent execution operations."""
from datetime import datetime, timezone


def now():
    return datetime.now(timezone.utc).isoformat()
