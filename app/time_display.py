"""Presentation-only timezone conversion; persisted historical UTC is untouched."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def turkey_time(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(ZoneInfo('Europe/Istanbul')).strftime('%d.%m.%Y %H:%M') + ' (Türkiye saati, UTC+03:00)'
