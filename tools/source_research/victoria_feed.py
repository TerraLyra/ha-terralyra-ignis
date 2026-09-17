"""Offline Victoria envelope research; no network, HA or permission assertion."""
import json
import math


class InvalidFeed(ValueError):
    """Incomplete, ambiguous or unsupported input; never an empty-feed result."""


def inspect_feed(payload: bytes, *, max_bytes=1_048_576, max_records=10_000):
    """Return original decoded records, without interpreting types or dates.

    Expected research schema is a results array of flat objects. Unknown scalar
    fields are preserved. Nested records require explicit schema review.
    """
    for limit in (max_bytes, max_records):
        if type(limit) is not int or limit <= 0:
            raise ValueError('Limits must be positive integers')
    if not isinstance(payload, bytes) or len(payload) > max_bytes:
        raise InvalidFeed('Invalid or oversized payload')
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise InvalidFeed('Duplicate JSON field')
            result[key] = value
        return result
    def constant(_):
        raise InvalidFeed('Non-finite JSON number')
    try:
        data = json.loads(payload.decode('utf-8-sig'), object_pairs_hook=pairs,
                          parse_constant=constant)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise InvalidFeed('Invalid JSON envelope') from error
    if not isinstance(data, dict) or set(data) != {'results'}:
        raise InvalidFeed('Expected results envelope')
    records = data['results']
    if not isinstance(records, list) or len(records) > max_records:
        raise InvalidFeed('Invalid results array')
    for record in records:
        if not isinstance(record, dict) or not record:
            raise InvalidFeed('Expected nonempty record')
        for value in record.values():
            if isinstance(value, (dict, list)):
                raise InvalidFeed('Nested record requires schema review')
            if isinstance(value, float) and not math.isfinite(value):
                raise InvalidFeed('Non-finite number')
    return tuple(records)


def summarize_feed(payload: bytes, **limits):
    """Fixed labels and counts only; no raw incident details in diagnostics."""
    records = inspect_feed(payload, **limits)
    return {'purpose': 'offline_source_research', 'status': 'experimental',
            'production_readiness': 'not_established', 'record_count': len(records)}
