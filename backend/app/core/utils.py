from datetime import UTC, datetime


def utcnow() -> datetime:
    """Current UTC time as naive datetime (for timestamp-without-timezone columns)."""
    return datetime.now(UTC).replace(tzinfo=None)
