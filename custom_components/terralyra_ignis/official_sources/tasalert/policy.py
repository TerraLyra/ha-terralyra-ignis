"""Pure research response policy, not an HTTP client or production scheduler."""
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from xml.etree.ElementTree import ParseError
from .kml import parse_kml
from .snapshot import compare_snapshots

INTERVAL = timedelta(minutes=30)  # Local conservative choice, not upstream permission.


@dataclass(frozen=True)
class State:
    snapshot: bytes | None = None
    etag: str | None = None
    failures: int = 0
    next_attempt: datetime | None = None
    status: str = 'not_requested'
    last_success_at: datetime | None = None


def request_headers(state):
    return {'If-None-Match': state.etag} if state.snapshot is not None and state.etag else {}


def apply_response(state, now, status, body=b'', etag=None, retry_after=None):
    """Keep accepted bytes on every failure or ambiguous replacement.

    Missing-record reconciliation is deliberately held for review. This policy
    does not establish retention expiry, record freshness, or a safe area.
    Callers must gate I/O on next_attempt before issuing a request.
    """
    if now.utcoffset() is None:
        raise ValueError('Aware receipt time required')
    if state.next_attempt and now < state.next_attempt:
        raise ValueError('Request not due')
    failures = state.failures + 1
    delay = min(INTERVAL * (2 ** min(failures - 1, 6)), timedelta(hours=24))
    deadline = now + delay
    if retry_after:
        try:
            if str(retry_after).isdigit():
                requested = now + timedelta(seconds=int(retry_after))
            else:
                requested = parsedate_to_datetime(retry_after)
                if requested.utcoffset() is None:
                    raise ValueError('Naive retry clock')
            deadline = max(deadline, requested)
        except (ValueError, TypeError, OverflowError):
            pass
    failed = replace(state, failures=failures, next_attempt=deadline, status='retrieval_failed')
    if status == 304:
        return (replace(state, failures=0, next_attempt=now+INTERVAL, status='not_modified', last_success_at=now)
                if state.snapshot is not None else replace(failed, status='unexpected_304'))
    if status != 200:
        return failed
    try:
        records = parse_kml(body)
        if not records:
            return replace(failed, status='empty_snapshot_review')
        if state.snapshot is not None:
            plan = compare_snapshots(state.snapshot, body)
            if any(c['state'] in ('not_in_snapshot', 'review_required') for c in plan['changes']):
                return replace(failed, status='replacement_review')
    except (ValueError, ParseError, UnicodeError):
        return replace(failed, status='invalid_snapshot')
    # Validators belong only to the accepted representation. Never adopt an
    # error/review ETag, which could hide a still-unaccepted response behind 304.
    safe_etag = etag if isinstance(etag,str) and len(etag)<=512 and not any(ord(c)<32 or ord(c)==127 for c in etag) else None
    return State(body, safe_etag, 0, now+INTERVAL, 'accepted', now)
