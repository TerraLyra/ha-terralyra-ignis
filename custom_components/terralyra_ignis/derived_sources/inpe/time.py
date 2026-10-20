"""UTC contract for detail fields; preserve date precision, never infer status."""
from datetime import date, datetime, timezone
import re

_DATE = re.compile(r'\d{4}-\d{2}-\d{2}\Z')
_STAMP = re.compile(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)?\Z')


def parse_source_time(value):
    """Return date, aware UTC datetime, or None; reject ambiguous representations.

    A date is a processing/calendar day, not a midnight detection. Callers must
    keep data_min/data_max distinct from data_ultimo_foco and retrieval time.
    """
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError('Expected INPE date or timestamp')
    if _DATE.fullmatch(value):
        return date.fromisoformat(value)
    if not _STAMP.fullmatch(value):
        raise ValueError('Unsupported INPE UTC timestamp')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return parsed.replace(tzinfo=timezone.utc)
