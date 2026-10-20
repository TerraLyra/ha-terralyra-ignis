"""Bounded offline detail parsing; no per-event polling or perimeter claims."""
from dataclasses import dataclass
from datetime import date, datetime
import json
from inpe_centroids import _pairs, _constant
from inpe_time import parse_source_time

MAX_DETAIL_BYTES = 1024 * 1024


@dataclass(frozen=True)
class EventTimes:
    source_id: int
    first_day: date | None
    last_day: date | None
    latest_hotspot: datetime | None


def parse_detail_times(payload: bytes, *, expected_id: int) -> EventTimes:
    """Only explicitly matched event IDs may contribute time information.

    Ignore geometry, HTML and unrelated fields. Day range describes the source
    product, not fire ignition/extinction. The hotspot may be newer than the
    previous-day geometry range; this is not an inconsistent response.
    """
    if type(expected_id) is not int or not 0 < expected_id < 2**63:
        raise ValueError('Invalid requested event ID')
    if not isinstance(payload, bytes) or not 0 < len(payload) <= MAX_DETAIL_BYTES:
        raise ValueError('Invalid detail payload size/type')
    try:
        data = json.loads(payload.decode('utf-8'), object_pairs_hook=_pairs,
                          parse_constant=_constant)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ValueError('Invalid detail JSON') from exc
    if (not isinstance(data, dict) or type(data.get('id_evento')) is not int
            or data['id_evento'] != expected_id or 'error' in data):
        raise ValueError('Unexpected detail event')
    first = parse_source_time(data.get('data_min'))
    last = parse_source_time(data.get('data_max'))
    latest = parse_source_time(data.get('data_ultimo_foco'))
    if any(value is not None and type(value) is not date for value in (first, last)):
        raise ValueError('Expected source calendar dates')
    if latest is not None and type(latest) is not datetime:
        raise ValueError('Expected precise latest hotspot timestamp')
    if first is not None and last is not None and first > last:
        raise ValueError('Reversed source day range')
    return EventTimes(expected_id, first, last, latest)


def time_report(times: EventTimes):
    """Explicit provenance/precision for later display, not incident lifecycle."""
    return {
        'source_id': times.source_id,
        'source_first_day_utc': times.first_day.isoformat() if times.first_day else None,
        'source_last_day_utc': times.last_day.isoformat() if times.last_day else None,
        'latest_hotspot_at_utc': times.latest_hotspot.isoformat() if times.latest_hotspot else None,
        'geometry_update_basis': 'previous_day',
        'provisional': True,
    }
